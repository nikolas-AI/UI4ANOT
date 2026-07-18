import open3d as o3d

pcd_ref = o3d.io.read_point_cloud("PointClouds\SRC\p02.ply")  # Replace with the actual path to your reference point cloud file
pcd_dist = o3d.io.read_point_cloud("PointClouds\PPC\p02_geocnn_r02.ply")  # Replace with the actual path to your distorted point cloud file


vis1 = o3d.visualization.Visualizer()
vis1.create_window(window_name="Reference", width=800, height=600, left=50, top=50)
vis1.add_geometry(pcd_ref)

vis2 = o3d.visualization.Visualizer()
vis2.create_window(window_name="Distorted", width=800, height=600, left=900, top=50)
vis2.add_geometry(pcd_dist)

opt1 = vis1.get_render_option()
opt2 = vis2.get_render_option()
opt1.point_size = 2.0
opt2.point_size = 2.0

while True:
    vis1.update_geometry(pcd_ref)
    vis2.update_geometry(pcd_dist)

    vis1.poll_events()
    vis2.poll_events()

    vis1.update_renderer()
    vis2.update_renderer()

    if not vis1.poll_events() or not vis2.poll_events():
        break

vis1.destroy_window()
vis2.destroy_window()

