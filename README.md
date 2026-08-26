# 🏥 Hospital Delivery Bot

> An autonomous mobile robot built with **ROS 2 Humble** + **Gazebo Classic 11** that navigates a simulated hospital ward, avoids dynamic human obstacles in real time, and delivers items between rooms — powered by the full **Nav2** stack.

---

## 📸 Demo

> **Replace the placeholder below with your recorded GIF (Gazebo + RViz side by side).**

<!-- ============================================================
     PASTE YOUR GIF HERE
     Recommended: record with peek, ffmpeg, or kazam
     Resize to ~900px wide for best GitHub rendering
     Example:
       ![Demo GIF](docs/demo.gif)
     ============================================================ -->

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│         [ INSERT GAZEBO + RVIZ GIF HERE ]           │
│       (robot navigating with walking humans)        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🗺️ SLAM Map

> **Replace the placeholder below with your saved SLAM map screenshot.**

<!-- ============================================================
     PASTE YOUR SLAM MAP IMAGE HERE
     The map was generated with slam_toolbox (online async mode)
     and saved to maps/hospital_ward.pgm + hospital_ward.yaml
     Example:
       ![SLAM Map](docs/slam_map.png)
     ============================================================ -->

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│           [ INSERT SLAM MAP IMAGE HERE ]            │
│    (hospital_ward.pgm rendered in RViz / image)     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Robot Hardware Spec (Simulated)](#-robot-hardware-spec-simulated)
- [Software Architecture](#-software-architecture)
- [World & Environment](#-world--environment)
- [Project Structure](#-project-structure)
- [Dependencies](#-dependencies)
- [Build & Install](#-build--install)
- [Running the Simulation](#-running-the-simulation)
  - [Phase 1 — SLAM Mapping](#phase-1--slam-mapping-build-the-map-first)
  - [Phase 2 — Autonomous Navigation](#phase-2--autonomous-navigation-uses-the-saved-map)
- [Sending Navigation Goals](#-sending-navigation-goals)
- [ROS 2 Topics & Nodes](#-ros-2-topics--nodes)
- [Nav2 Configuration Details](#-nav2-configuration-details)
- [Dynamic Human Obstacles](#-dynamic-human-obstacles)
- [Troubleshooting](#-troubleshooting)

---

## 🔍 Overview

The **Hospital Delivery Bot** is a fully simulated autonomous ground vehicle designed to operate inside a multi-room hospital ward. It demonstrates the complete robotics autonomy pipeline:

1. **Sensing** — 360° 2D LiDAR (`/scan`) detects walls, furniture, and moving people
2. **Mapping** — SLAM Toolbox builds an occupancy grid map from scratch via teleoperation
3. **Localisation** — AMCL (Adaptive Monte Carlo Localisation) places the robot on the saved map using particle filters
4. **Planning** — NavFn global planner computes a cost-optimal path to the goal
5. **Control** — DWB (Dynamic Window Approach) local planner steers the robot while avoiding live obstacles
6. **Behaviour** — Nav2 Behaviour Trees manage retries, recoveries (spin, back-up), and goal execution

The whole system runs entirely in simulation on a single machine — no physical hardware required.

---

## 🤖 Robot Hardware Spec (Simulated)

| Component | Details |
|-----------|---------|
| **Drive** | Differential drive — 2 powered wheels, 1 passive front caster |
| **Chassis** | 0.50 m (L) × 0.40 m (W) × 0.20 m (H), 15 kg |
| **Wheel separation** | 0.45 m |
| **Wheel radius** | 0.10 m |
| **Max linear speed** | 0.30 m/s |
| **Max angular speed** | 1.0 rad/s |
| **LiDAR** | 360° horizontal, 0.12 – 8.0 m range, 360 samples/rev, 10 Hz |
| **Odometry** | Published by `gazebo_ros_diff_drive` plugin at 30 Hz |
| **TF root frame** | `base_footprint` (ground-plane projection, required by Nav2) |

The robot URDF is defined in [`urdf/hospital_bot.urdf.xacro`](urdf/hospital_bot.urdf.xacro) using proper inertia macros for physics stability. All Gazebo plugins publish native ROS 2 topics — no extra bridge node is needed.

---

## 🏗️ Software Architecture

```
Gazebo Classic 11
  └─ hospital_ward.world
       ├─ hospital_bot (spawned via spawn_entity.py)
       │    ├─ libgazebo_ros_diff_drive  → /cmd_vel, /odom, TF odom→base_footprint
       │    ├─ libgazebo_ros_ray_sensor  → /scan
       │    └─ libgazebo_ros_joint_state_publisher → /joint_states
       └─ 4× animated human actors (walk.dae)

robot_state_publisher → TF base_footprint→base_link→laser

─────────────────────── NAV2 STACK ───────────────────────────────
map_server      → reads hospital_ward.yaml  → /map
amcl            → /scan + /map              → /amcl_pose, TF map→odom
planner_server  → NavFn global planner      → /plan
controller_server→ DWB local planner        → /cmd_vel, /local_plan
bt_navigator    → orchestrates everything   → /navigate_to_pose
behavior_server → spin / backup / wait
velocity_smoother→ smoothed /cmd_vel output
lifecycle_manager→ manages node transitions
──────────────────────────────────────────────────────────────────

RViz 2
  ├─ Map display            (/map)
  ├─ LaserScan display      (/scan)
  ├─ RobotModel display     (/robot_description)
  ├─ Global Plan            (/plan)
  ├─ Local Plan             (/local_plan)
  ├─ AMCL Particles         (/particlecloud)
  ├─ AMCL Pose              (/amcl_pose)
  └─ Tools: SetInitialPose, SetGoal (2D Goal Pose)
```

---

## 🏨 World & Environment

The hospital ward (`worlds/hospital_ward.world`) is a hand-crafted **16 m × 12 m** SDF environment:

- **6 rooms** divided by interior walls with 1 m doorways
- **Main central corridor** connecting all rooms
- **14 static obstacles** across all rooms (boxes, cylinders, spheres representing beds, IV poles, equipment carts, etc.) — these give SLAM/LiDAR distinct features to latch onto
- **4 animated walking actors** using Gazebo's built-in `walk.dae` skinned mesh:

| Actor | Role | Patrol Zone |
|-------|------|-------------|
| `walking_person` | Generic staff | Main corridor (East ↔ West) |
| `walking_nurse` | Nurse | Upper rooms (top corridor) |
| `walking_doctor` | Doctor | Lower rooms (L-shaped route) |
| `walking_visitor` | Visitor | East side (North ↔ South) |

> ⚠️ The actors are **purely dynamic** — they are **not baked into the SLAM map**. Nav2's local costmap detects them in real time via `/scan` and routes around them on the fly.

---

## 📁 Project Structure

```
hospital_delivery_bot/
├── CMakeLists.txt                  # CMake build file (ament_cmake)
├── package.xml                     # ROS 2 package manifest & dependencies
│
├── urdf/
│   └── hospital_bot.urdf.xacro     # Full robot description (chassis, wheels, LiDAR, plugins)
│
├── worlds/
│   └── hospital_ward.world         # SDF world: rooms, walls, obstacles, 4 walking humans
│
├── maps/
│   ├── hospital_ward.pgm           # Occupancy grid image (generated by SLAM)
│   └── hospital_ward.yaml          # Map metadata (resolution, origin, thresholds)
│
├── config/
│   ├── nav2_params.yaml            # Full Nav2 parameter file (AMCL, planners, costmaps…)
│   ├── slam_params.yaml            # SLAM Toolbox parameters (online async mode)
│   └── rviz_config.rviz            # RViz layout (map, scan, robot, paths, AMCL particles)
│
├── launch/
│   ├── gazebo.launch.py            # Gazebo + robot spawn only
│   ├── slam.launch.py              # SLAM Toolbox only
│   ├── mapping.launch.py           # Gazebo + SLAM + RViz  (for building the map)
│   └── navigation.launch.py        # Gazebo + Nav2 + RViz  (for autonomous navigation)
│
└── hospital_delivery_bot/
    ├── __init__.py
    ├── delivery_node.py            # Delivery waypoint sequencer node
    └── simple_teleop.py            # Minimal keyboard teleop helper
```

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `ros-humble-nav2-bringup` | Nav2 bringup launch files |
| `ros-humble-nav2-amcl` | Monte Carlo localisation |
| `ros-humble-nav2-map-server` | Static map server |
| `ros-humble-nav2-planner` | Global path planner (NavFn) |
| `ros-humble-nav2-controller` | Local controller (DWB) |
| `ros-humble-nav2-behaviors` | Recovery behaviours |
| `ros-humble-nav2-bt-navigator` | Behaviour tree executor |
| `ros-humble-nav2-lifecycle-manager` | Lifecycle management |
| `ros-humble-nav2-costmap-2d` | 2D costmap layers |
| `ros-humble-slam-toolbox` | Online async SLAM |
| `ros-humble-gazebo-ros-pkgs` | Gazebo ↔ ROS 2 bridge |
| `ros-humble-robot-state-publisher` | TF from URDF |
| `ros-humble-rviz2` | Visualisation |
| `ros-humble-teleop-twist-keyboard` | Keyboard teleoperation |
| `ros-humble-xacro` | URDF macro processor |

Install all at once:
```bash
sudo apt update
sudo apt install -y \
  ros-humble-nav2-bringup \
  ros-humble-slam-toolbox \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-robot-state-publisher \
  ros-humble-rviz2 \
  ros-humble-teleop-twist-keyboard \
  ros-humble-xacro
```

---

## 🔧 Build & Install

```bash
# 1. Clone into your workspace src/
cd ~/Desktop/hospital_ws/src
# (repo is already symlinked as hospital_delivery_bot)

# 2. Build
cd ~/Desktop/hospital_ws
colcon build --symlink-install --packages-select hospital_delivery_bot

# 3. Source the workspace (add to ~/.bashrc to make permanent)
source ~/Desktop/hospital_ws/install/setup.bash
```

> **Tip:** Add `source ~/Desktop/hospital_ws/install/setup.bash` to your `~/.bashrc` so you never get `command not found` on `ros2 launch`.

---

## 🚀 Running the Simulation

### Phase 1 — SLAM Mapping *(build the map first)*

> Skip this phase if you already have the map files in `maps/`. The repo ships with `hospital_ward.pgm` + `hospital_ward.yaml` ready to use.

**Terminal 1 — Launch Gazebo + SLAM + RViz**
```bash
source ~/Desktop/hospital_ws/install/setup.bash
ros2 launch hospital_delivery_bot mapping.launch.py
```

**Terminal 2 — Keyboard Teleop** *(needs its own TTY)*
```bash
source ~/Desktop/hospital_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Drive the robot around the entire ward until the RViz map looks complete with no large grey (unknown) areas. Then save the map:

**Terminal 3 — Save the map**
```bash
source ~/Desktop/hospital_ws/install/setup.bash
ros2 run nav2_map_server map_saver_cli \
  -f ~/Desktop/hospitaldelivry_bot/maps/hospital_ward
```

This writes `hospital_ward.pgm` and `hospital_ward.yaml`.

---

### Phase 2 — Autonomous Navigation *(uses the saved map)*

**Terminal 1 — Start everything**
```bash
source ~/Desktop/hospital_ws/install/setup.bash
ros2 launch hospital_delivery_bot navigation.launch.py
```

This single command starts:
- Gazebo with the hospital world and all 4 walking humans
- Nav2 full stack (map_server, AMCL, planner, controller, BT navigator, behaviours, lifecycle manager)
- RViz pre-configured with the Nav2 toolset

**What to expect at startup:**
1. Gazebo opens with the ward and the robot spawned at `(0, -1.5)`
2. RViz opens showing the map, the robot model, and purple AMCL particles around the spawn point
3. AMCL is pre-seeded at the spawn pose — the robot **does not need a manual 2D Pose Estimate**
4. Wait ~5 seconds for all Nav2 nodes to activate (lifecycle transitions happen automatically)

---

## 🎯 Sending Navigation Goals

### Via RViz *(easiest)*
1. Click **"2D Goal Pose"** in the RViz toolbar (or press **G**)
2. Click a point on the map and drag to set the orientation
3. Nav2 plans a path immediately and the robot starts driving

### Via Terminal
```bash
source ~/Desktop/hospital_ws/install/setup.bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 2.0, y: 1.0, z: 0.0}, orientation: {w: 1.0}}}}"
```

### Check Nav2 is fully alive
```bash
source ~/Desktop/hospital_ws/install/setup.bash
ros2 node list | grep -E "amcl|bt_navigator|planner|controller|map_server"
```

Expected output:
```
/amcl
/bt_navigator
/controller_server
/map_server
/planner_server
```

---

## 📡 ROS 2 Topics & Nodes

### Key Topics

| Topic | Type | Direction | Description |
|-------|------|-----------|-------------|
| `/scan` | `sensor_msgs/LaserScan` | Published | 360° LiDAR at 10 Hz |
| `/odom` | `nav_msgs/Odometry` | Published | Wheel odometry at 30 Hz |
| `/cmd_vel` | `geometry_msgs/Twist` | Subscribed | Velocity commands to robot |
| `/map` | `nav_msgs/OccupancyGrid` | Published | Static occupancy grid |
| `/amcl_pose` | `geometry_msgs/PoseWithCovarianceStamped` | Published | Best AMCL pose estimate |
| `/particlecloud` | `geometry_msgs/PoseArray` | Published | AMCL particle cloud |
| `/plan` | `nav_msgs/Path` | Published | Global plan (green in RViz) |
| `/local_plan` | `nav_msgs/Path` | Published | Local DWB plan (red in RViz) |
| `/goal_pose` | `geometry_msgs/PoseStamped` | Subscribed | Goal from RViz 2D Goal tool |

### TF Tree

```
map
 └─ odom          (published by AMCL)
      └─ base_footprint   (published by diff_drive plugin)
           └─ base_link   (fixed joint)
                ├─ left_wheel
                ├─ right_wheel
                ├─ caster_wheel
                └─ laser
```

---

## ⚙️ Nav2 Configuration Details

The full parameter file lives at [`config/nav2_params.yaml`](config/nav2_params.yaml). Key tuning decisions:

### AMCL
- **`base_frame_id: base_footprint`** — matches the diff-drive plugin's TF output
- **`set_initial_pose: true`** with `x: 0.0, y: -1.5` — automatically seeds the particle filter at the Gazebo spawn pose; no manual 2D Pose Estimate needed
- **`laser_max_range: 8.0`** — matches the LiDAR in the URDF

### Costmaps & Footprint
- **Footprint polygon** `[[0.25, 0.2], [0.25, -0.2], [-0.25, -0.2], [-0.25, 0.2]]` replaces the default circular `robot_radius`
- The ward's doorways are ~1 m wide; a circular approximation would make them nearly impassable. The true rectangle (inscribed radius 0.2 m) leaves usable clearance
- **`inflation_radius: 0.45 m`** — just under half the doorway width so the doorway centre-line stays at zero cost

### DWB Local Planner
- **`max_vel_x: 0.30`** and **`acc_lim_x: 1.0`** — the Gazebo diff-drive plugin caps acceleration, so overpromising causes overshoot in tight spaces
- **`sim_time: 1.7 s`** — enough lookahead to smooth around moving humans

---

## 🚶 Dynamic Human Obstacles

The world contains **4 animated walking actors** using Gazebo's built-in `walk.dae` skinned mesh. They are **not part of the static map** — SLAM was run before they start affecting the environment meaningfully. Nav2's **VoxelLayer** in the local costmap sees them via `/scan` and routes around them in real time.

| Actor name | Patrol description | Loop time |
|------------|--------------------|-----------|
| `walking_person` | Main corridor, East ↔ West | 21 s |
| `walking_nurse` | Upper rooms top corridor | 29 s |
| `walking_doctor` | Lower rooms L-shaped route | 33.5 s |
| `walking_visitor` | East side North ↔ South | 21 s |

Each actor has a staggered `delay_start` (0 s, 2 s, 4 s, 6 s) so they don't all begin at the same position.

---

## 🛠️ Troubleshooting

### `command not found: ros2`
You need to source ROS 2 and the workspace:
```bash
source /opt/ros/humble/setup.bash
source ~/Desktop/hospital_ws/install/setup.bash
```
Add both lines to `~/.bashrc`.

### Gazebo opens but robot is not visible / falls through the floor
The robot spawns with `z=0.2`. If Gazebo physics pushes it away, check that the `base_footprint` joint in the URDF positions wheels at ground level. Rebuild after any URDF change:
```bash
colcon build --symlink-install --packages-select hospital_delivery_bot
```

### AMCL particles do not converge / robot gets lost
- The particle filter is pre-seeded at `(0, -1.5)` — if you change the spawn pose in `gazebo.launch.py`, update `initial_pose` in `nav2_params.yaml` to match
- Drive the robot a short distance first (use teleop) to trigger filter updates

### Nav2 nodes not found after launch
Wait 10–15 seconds for lifecycle transitions to complete. Check with:
```bash
ros2 node list | grep -E "amcl|planner|controller|bt_navigator"
```

### Goal is rejected immediately
- Ensure the goal is in **free space** on the map (white area in RViz)
- Check that `amcl_pose` is being published: `ros2 topic echo /amcl_pose`

### Map not loading / blank white map in RViz
Verify the map file path in `nav2_params.yaml` → `map_server.yaml_filename` or pass it explicitly:
```bash
ros2 launch hospital_delivery_bot navigation.launch.py \
  map:=/absolute/path/to/maps/hospital_ward.yaml
```

---

## 📄 License

Apache 2.0 — see [LICENSE](LICENSE) for details.

---

*Built with ROS 2 Humble · Gazebo Classic 11 · Nav2 · SLAM Toolbox*
