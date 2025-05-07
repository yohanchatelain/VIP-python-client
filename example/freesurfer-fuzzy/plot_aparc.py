import numpy as np
import nibabel as nib
from nibabel.gifti import gifti
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import scipy.ndimage
from skimage import measure
import argparse
import os
import sys
import plotly.colors as pc
import pandas as pd

from icecream import ic
ic.configureOutput(includeContext=True, contextAbsPath=False)

def load_gifti_surface(gifti_file):
    """
    Load a GIFTI surface file (.gii) and return vertices and faces.
    
    Args:
        gifti_file: Path to the GIFTI file
        
    Returns:
        vertices: numpy array of shape (n_vertices, 3)
        faces: numpy array of shape (n_faces, 3)
    """
    # Load the GIFTI file
    gii = nib.load(gifti_file)
    
    # GIFTI files typically have two data arrays:
    # - First array: vertices (coordinates)
    # - Second array: faces (triangles)
    if len(gii.darrays) < 2:
        # Some GIFTI files might have only vertices or might be formatted differently
        print(f"Warning: {gifti_file} has {len(gii.darrays)} data arrays instead of the expected 2")
        
    # Extract vertices and faces based on file structure
    if len(gii.darrays) >= 2:
        # Standard format with vertices and faces
        vertices = gii.darrays[0].data
        faces = gii.darrays[1].data
    else:
        # Handle special cases or throw an error
        raise ValueError(f"Unable to extract both vertices and faces from {gifti_file}")
    
    return vertices, faces

def load_gifti_labels(gifti_file):
    """
    Load a GIFTI labels file (.gii) and return the labels.
    
    Args:
        gifti_file: Path to the GIFTI labels file

    Returns:
        labels: numpy array of shape (n_vertices,)
    """
    # Load the GIFTI file
    gii = nib.load(gifti_file)
    
    # Extract labels from the first data array
    if len(gii.darrays) > 0:
        labels = gii.darrays[0].data
        # map id to label_name
        labels_name = gii.labeltable.get_labels_as_dict()
        labelname_color_map = {}
        for giilabel in gii.labeltable.labels:
            labelname_color_map[giilabel.label] = pc.label_rgb(giilabel.rgba)
        
    else:
        raise ValueError(f"No data arrays found in {gifti_file}")
    
    return labels, labels_name, labelname_color_map


def apply_transformation(vertices, transformation_matrix):
    """
    Apply an affine transformation to the vertices.
    
    Args:
        vertices: numpy array of shape (n_vertices, 3)
        transformation_matrix: 4x4 affine transformation matrix
        
    Returns:
        transformed_vertices: numpy array of shape (n_vertices, 3)
    """
    # Add homogeneous coordinate (make it 4D)
    vertices_homog = np.hstack((vertices, np.ones((vertices.shape[0], 1))))
    
    # Apply transformation
    transformed_vertices = np.dot(vertices_homog, transformation_matrix.T)[:, :3]
    
    return transformed_vertices

def smooth_mesh(vertices, faces, iterations=10, relaxation=0.1):
    """
    Apply Laplacian smoothing to the mesh.
    
    Args:
        vertices: numpy array of shape (n_vertices, 3)
        faces: numpy array of shape (n_faces, 3)
        iterations: Number of smoothing iterations
        relaxation: Relaxation factor (0-1)
        
    Returns:
        smoothed_vertices: numpy array of shape (n_vertices, 3)
    """
    # Create a copy of the vertices to modify
    smoothed_vertices = vertices.copy()
    
    # Create adjacency list for each vertex
    adjacency = [[] for _ in range(len(vertices))]
    for face in faces:
        for i in range(3):
            v1 = face[i]
            v2 = face[(i + 1) % 3]
            adjacency[v1].append(v2)
            adjacency[v2].append(v1)
    
    # Remove duplicates in adjacency lists
    adjacency = [list(set(adj)) for adj in adjacency]
    
    # Perform Laplacian smoothing
    for _ in range(iterations):
        new_vertices = smoothed_vertices.copy()
        for i in range(len(smoothed_vertices)):
            if adjacency[i]:
                # Calculate centroid of neighbors
                neighbor_centroid = np.mean([smoothed_vertices[j] for j in adjacency[i]], axis=0)
                # Move vertex towards centroid based on relaxation factor
                new_vertices[i] = smoothed_vertices[i] + relaxation * (neighbor_centroid - smoothed_vertices[i])
        smoothed_vertices = new_vertices
    
    return smoothed_vertices

def decimate_mesh(vertices, faces, reduction_factor=0.5):
    """
    Reduce the number of faces in the mesh.
    This is a simple implementation for demonstration.
    For production use, consider using a library like PyMesh or Open3D.
    
    Args:
        vertices: numpy array of shape (n_vertices, 3)
        faces: numpy array of shape (n_faces, 3)
        reduction_factor: Factor by which to reduce the mesh (0-1)
        
    Returns:
        decimated_vertices: numpy array of shape (n_vertices_new, 3)
        decimated_faces: numpy array of shape (n_faces_new, 3)
    """
    # For a proper implementation, use a dedicated library
    # This is a simplistic approach that just takes a subset of faces
    num_faces_new = int(len(faces) * reduction_factor)
    indices = np.random.choice(len(faces), num_faces_new, replace=False)
    decimated_faces = faces[indices]
    
    # Remap vertex indices to create a new, smaller vertex array
    used_vertices = np.unique(decimated_faces.flatten())
    vertex_map = {old_idx: new_idx for new_idx, old_idx in enumerate(used_vertices)}
    
    decimated_vertices = vertices[used_vertices]
    
    # Remap face indices
    for i in range(len(decimated_faces)):
        for j in range(3):
            decimated_faces[i, j] = vertex_map[decimated_faces[i, j]]
    
    return decimated_vertices, decimated_faces

def visualize_mesh(vertices, faces, labels):
    """
    Visualize the mesh using Plotly for interactive 3D visualization.
    
    Args:
        vertices: numpy array of shape (n_vertices, 3)
        faces: numpy array of shape (n_faces, 3)
    """
    # Create a mesh3d trace for Plotly
    # Plotly requires faces as three separate arrays i, j, k
    i = faces[:, 0]
    j = faces[:, 1]
    k = faces[:, 2]
    
    # Create the 3D mesh
    mesh = go.Mesh3d(
        x=vertices[:, 0],
        y=vertices[:, 1],
        z=vertices[:, 2],
        i=i, j=j, k=k,
        opacity=0.8,
        colorscale=[[0, 'blue'], [1, 'lightblue']],
        intensity=vertices[:, 2],  # Color by z-coordinate
        showscale=False
    )
    
    # Create the figure
    fig = go.Figure(data=[mesh])
    
    # Update layout for better visualization
    fig.update_layout(
        scene=dict(
            xaxis=dict(title='X'),
            yaxis=dict(title='Y'),
            zaxis=dict(title='Z'),
            aspectmode='cube'  # Equal aspect ratio
        ),
        width=900,
        height=700,
        margin=dict(l=0, r=0, b=0, t=30),
        title="3D Mesh Visualization"
    )
    
    # Show the figure
    fig.show()

def save_mesh_to_obj(vertices, faces, output_file):
    """
    Save the mesh to an OBJ file.
    
    Args:
        vertices: numpy array of shape (n_vertices, 3)
        faces: numpy array of shape (n_faces, 3)
        output_file: Path to the output OBJ file
    """
    with open(output_file, 'w') as f:
        # Write vertices
        for vertex in vertices:
            f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")
        
        # Write faces (OBJ uses 1-indexed vertices)
        for face in faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Process GIFTI mesh files.')
    
    # Required arguments
    parser.add_argument('--gii', type=str, help='Input GIFTI file (.gii)')
    parser.add_argument('--gii-labels', type=str, help='Input GIFTI labels file (.gii)')
    parser.add_argument('--gii-surface', type=str, help='Input GIFTI surface file (.gii)')
    parser.add_argument("--hemisphere", type=str, required=True, help="Hemisphere (lh or rh)")
    
    # Optional arguments
    parser.add_argument('--output', '-o', type=str, help='Output html file', default='output.html')
    parser.add_argument('--smooth', '-s', action='store_true', help='Apply smoothing to the mesh')
    parser.add_argument('--iterations', '-i', type=int, default=20, help='Number of smoothing iterations')
    parser.add_argument('--relaxation', '-r', type=float, default=0.2, help='Smoothing relaxation factor (0-1)')
    parser.add_argument('--decimate', '-d', action='store_true', help='Decimate (simplify) the mesh')
    parser.add_argument('--reduction', type=float, default=0, help='Decimation reduction factor (0-1)')
    parser.add_argument('--visualize', '-v', action='store_true', help='Visualize the meshes')
    parser.add_argument('--no-save', action='store_true', help='Do not save the output mesh')
    parser.add_argument('--stats-file', type=str, help='Path to the stats file')
    parser.add_argument('--intensity-max', type=float, help='Maximum intensity for color mapping')
    parser.add_argument('--intensity-min', type=float, help='Minimum intensity for color mapping')
    parser.add_argument('--title', type=str, default="Freesurfer Surface", help='Title for the visualization')
    
    return parser.parse_args()


def check_gifti_file(gifti_file):
    # Check if input file exists
    if not os.path.exists(gifti_file):
        raise FileNotFoundError(f"Input file '{gifti_file}' does not exist")
    

def intensity_to_rgb(colormap, low=0, high=1, npoints=101):
    colorscale = pc.get_colorscale(colormap)
    return pc.sample_colorscale(colorscale, npoints, low=low, high=high)


def main():
    """Main function to process GIFTI files"""
    # Parse command line arguments
    args = parse_args()
    
    # Load the GIFTI file
    if args.gii:
        check_gifti_file(args.gii)
        print(f"Loading {args.input_file}...")
        vertices, faces = load_gifti_surface(args.input_file)
        print(f"Loaded mesh with {len(vertices)} vertices and {len(faces)} faces")
    elif args.gii_labels and args.gii_surface:
        check_gifti_file(args.gii_labels)
        check_gifti_file(args.gii_surface)
        print(f"Loading {args.gii_labels} and {args.gii_surface}...")
        vertices, faces = load_gifti_surface(args.gii_surface)
        labels, labels_name_map, labels_color_map = load_gifti_labels(args.gii_labels)
        print(f"Loaded mesh with {len(vertices)} vertices and {len(faces)} faces")
    else:
        print("Error: Please provide either --gii or both --gii-labels and --gii-surface")
        return 1
    
    # Keep track of original and processed vertices/faces
    orig_vertices, orig_faces = vertices.copy(), faces.copy()
    processed_vertices, processed_faces = vertices.copy(), faces.copy()
    
    # Apply smoothing if requested
    if args.smooth:
        print(f"Smoothing mesh with {args.iterations} iterations and relaxation={args.relaxation}...")
        processed_vertices = smooth_mesh(processed_vertices, processed_faces, 
                                            iterations=args.iterations, 
                                            relaxation=args.relaxation)
    
    # Apply decimation if requested
    if args.decimate:
        print(f"Decimating mesh with reduction factor={args.reduction}...")
        processed_vertices, processed_faces = decimate_mesh(processed_vertices, processed_faces, 
                                                            reduction_factor=args.reduction)
        print(f"Decimated mesh has {len(processed_vertices)} vertices and {len(processed_faces)} faces")
    
    # Visualize the meshes if requested
    print("Visualizing meshes...")
    

    # Add processed mesh
    i_proc = processed_faces[:, 0]
    j_proc = processed_faces[:, 1]
    k_proc = processed_faces[:, 2]

    ic(f"Labels: {labels.shape}")
    ic(f"Labels: {labels}")
    print("Original labels...")
    ic(f"Vertices: {vertices.shape}")
    ic(f"Faces: {faces.shape}")
    print("Processing labels...")
    ic(f"Vertices: {processed_vertices.shape}")
    ic(f"Faces: {processed_faces.shape}")
    # Create a color map for the labels

    hemi = args.hemisphere
    if hemi.lower().startswith('l'):
        hemi= 'lh'
    elif hemi.lower().startswith('r'):
        hemi= 'rh'
    else:
        raise ValueError(f"Invalid hemisphere '{args.hemisphere}'. Use 'lh' or 'rh'.")
    
    if args.stats_file:
        stats = pd.read_csv(args.stats_file)
        stats = stats[stats['hemi'] == hemi]
        min_ratio = stats['r'].min() if args.intensity_min is None else args.intensity_min
        max_ratio = stats['r'].max() if args.intensity_max is None else args.intensity_max
        cmap = intensity_to_rgb('RdYlGn_r', low=0, high=1)

        colors = []
        intensity = []
        labels_name = []
        for label in labels:            
            label_name = labels_name_map[label]
            labels_name.append(label_name)
            try:
                ratio = stats.loc[(stats['ROI'] == label_name), 'r'].values[0]
                ratio_normalized = (ratio - min_ratio) / (max_ratio - min_ratio)
                color_rgb = cmap[int(ratio_normalized * 100)]
            except IndexError:
                color_rgb = pc.qualitative.Dark2[-1]
                ratio = 0
                
            intensity.append(ratio)
            colors.append(color_rgb)
            
        vertexcolor = np.array(colors)
        intensity = np.array(intensity)

    # Create the mesh trace with matte material properties
    darkgray = pc.qualitative.Dark2[-1]

    cmap = pc.get_colorscale('RdYlGn_r')
    
    ic(cmap)

    x = pc.make_colorscale(colors=['gray','green','yellow','red'],
                           scale=[0,0.01,.5,1])
    ic(x)
    
    processed_brain = go.Mesh3d(
        x=vertices[:, 0],
        y=vertices[:, 1],
        z=vertices[:, 2],
        i=i_proc, j=j_proc, k=k_proc,
        opacity=1,
        colorscale=x,
        #vertexcolor=vertexcolor,
        # color bar title: numerical/anatomical variability
        colorbar=dict(
            title='Numerical/Anatomical Ratio',
        ),
        cmax=max_ratio,
        cmin=min_ratio,
        intensitymode='vertex',
        intensity=intensity,
        showscale=True,
        name='Processed',
        hoverinfo='text',
        text=labels_name,
        hovertemplate='<b>Label</b>: %{text}<br>' +
                      '<b>Intensity</b>: %{intensity:.2f}<br>',
                      
        # These parameters create the matte effect
        lighting=dict(
            ambient=0.8,      # Higher ambient light for matte effect
            diffuse=0.2,      # Lower diffuse for less shine
            roughness=0.9,    # High roughness for matte finish
            specular=0.01,    # Very low specular for no shine
            fresnel=0.01      # Low fresnel for matte look
        ),
        lightposition=dict(
            x=100,
            y=200,
            z=150
        ),
        flatshading=False      # Enable flat shading for matte look
    )
    
    fig = go.Figure(data=[processed_brain])

    # Remove grid and lines from the 3D scene
    # Remove background color
    fig.update_layout(
        scene=dict(
            xaxis=dict(showgrid=False, zeroline=False, showline=False, showticklabels=False, backgroundcolor='rgba(0,0,0,0)'),
            yaxis=dict(showgrid=False, zeroline=False, showline=False, showticklabels=False,
                       backgroundcolor='rgba(0,0,0,0)'),
            zaxis=dict(showgrid=False, zeroline=False, showline=False, showticklabels=False,
                       backgroundcolor='rgba(0,0,0,0)'),
            
        )
    )
    
    # Update layout
    fig.update_layout(
        title=args.title,
        height=700,
        width=1200,
        scene=dict(aspectmode='data')        ,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
    )

    
    if args.visualize:
        fig.show()
    
    # Save the processed mesh to OBJ file if not disabled
    if not args.no_save:
        print(f"Saving processed mesh to {args.output}...")
        fig.write_html(args.output)
        print(f"Saved processed mesh to {args.output}")
    
    return 0
        

# Run the main function if this script is executed directly
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"An error occurred: {e}")
        traceback.print_exc()
        sys.exit(1)
