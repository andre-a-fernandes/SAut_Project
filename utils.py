import numpy as np
import math
from sensor_msgs import point_cloud2

def sim_measurements(x: np.ndarray, Qt, lt) -> np.ndarray:
    """
    Simulate noisy range-bearing observation of the subset
    of landmarks in the robot's field of view, given the true pose.

    ## Parameters

    x : true robot pose

    Qt : measurement noise Cov. matrix (estim. of noise variance)

    lt : landmark map (n_landmarks, 3)

    ## Returns

    obs : simulated [range, bearing, id] observations - (n_observed, 3)

    """
    # Speficic Parameters
    fov = np.deg2rad(80)
    MAX_RANGE = 8

    observation = []  
    fovL = (x[2] + fov/2 + 2*np.pi) % (2*np.pi)
    fovR = (x[2] - fov/2 + 2*np.pi) % (2*np.pi)
    
    for landmark in lt:
        rel_angle = np.arctan2(landmark[1] - x[1], landmark[0] - x[0])
        rel_angle_2pi = (rel_angle + 2*np.pi) % (2*np.pi)
        
        # Only add measurement if it is inside the cone of vision
        if (fovL - rel_angle_2pi + np.pi) % (2*np.pi) - np.pi > 0 and (fovR - rel_angle_2pi + np.pi) % (2*np.pi) - np.pi < 0:
            range = np.sqrt(np.power(landmark[1] - x[1], 2) + np.power(landmark[0] - x[0], 2)) + Qt[0][0]*np.random.randn(1)
            bearing = (rel_angle - x[2] + Qt[1][1]*np.random.randn(1) + np.pi) % (2*np.pi) - np.pi
            if range[0] < MAX_RANGE:
                observation.append([range[0], bearing[0], landmark[2]])
            
    return np.array(observation), fov

def update_3Dplot(i, line, data):
    """
    Return the new point cloud to be plotted;
    used for a matplotlib `FuncAnimation`.
    """
    line.set_data(data[i, :, 2], data[i, :, 0])
    line.set_3d_properties(data[i, :, 1])
    return line,

def update_2Dplot(i, line, data):
    """
    Return the new surface of points to be
    displayed using matplotlib's `FuncAnimation`.
    """
    line.set_data(data[i, :, 2], data[i, :, 0])
    return line,

def create_pointcloud(data) -> np.ndarray:
    """
    Extract list of points from the PointCloud2 messages.

    ## Parameters

    data : individual ROS (point_cloud2) message

    ## Returns

    cloud : list of points (3D coordinates and intensity)
    """
    #assert isinstance(data, PointCloud2)
    gen = point_cloud2.read_points(data)
    
    # Declare pointcloud as list
    cloud = []
    i = 0;
    for p in gen:
        # Print instead a count of points
        if i == 0:
            print("First Point:", p)
        cloud.append(p)
        i += 1
    
    return np.array(cloud)  


def euler_from_quaternion(x: float, y: float, z: float, w: float):
    """
    Convert a quaternion (`x`,`y`,`z`,`w`) into Euler angles (roll, pitch, yaw).

    ## Parameters

    x : first quaternion vector coordinate
    y : second quaternion vector coordinate
    z : third quaternion vector coordinate
    w : quaternion scalar part

    ## Returns

    roll : rotation around x in radians (counterclockwise)
    pitch : rotation around y in radians (counterclockwise)
    yaw : rotation around z in radians (counterclockwise)

    """
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll_x = math.atan2(t0, t1)

    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch_y = math.asin(t2)

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw_z = math.atan2(t3, t4)

    return roll_x, pitch_y, yaw_z  # in radians


def p_multivariate_normal(x, mean, sigma):
    """
    Computes the probability of an arbitrary array (state) 
    given that the underlying random variable is normally 
    distributed.

    ## Parameters

    x : r.v realization                              (n, 1)
    mean : mean value for the r.v                    (n, 1)
    sigma : along with 'mean' parametrizes the r.v   (n, n)

    ## Returns

    p : probability of the realization `x`
    """
    x = np.array(x)
    mean = np.array(mean)
    exponent = -0.5 * np.transpose(x-mean) @ np.linalg.inv(sigma) @ (x-mean)
    return math.exp(exponent) / math.sqrt(np.linalg.det(2*math.pi*sigma))


def draw_cov_ellipse(mean, sigma, ax=None):
    """
    From center point (mean) and Cov. matrix (sigma) draw 
    error ellipse onto a plot.
    """
    # Get ellipse orientation and axes lengths
    lambdas, vectors = np.linalg.eig(sigma)
    idx = np.argsort(lambdas)[1]

    # Create the CI-95% ellipse
    z = np.arange(0, 2*np.pi, 0.01)
    xpos = 2*math.sqrt(5.991*lambdas[0])*np.cos(z)
    ypos = 2*math.sqrt(5.991*lambdas[1])*np.sin(z)
    # Rotate throught the eigenvectors
    theta = np.arctan(vectors[idx][1]/(vectors[idx][0] + 1e-9))
    new_xpos = mean[0] + xpos*np.cos(theta)+ypos*np.sin(theta)
    new_ypos = mean[1] - xpos*np.sin(theta)+ypos*np.cos(theta)

    # Actually plot the ellipse
    if ax is None:
        ax = plt.gca()
    #plt.plot(xpos, ypos, 'b-')
    ax.plot(new_xpos, new_ypos, 'gray')


    # Testing with 2D problem
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    MEAN = [1, 1]
    SIGMA = np.array([[1, 0.2],
                      [0.2, 1]])
    mmm = [2, 3]
    sss = np.array([[1, 0],
                    [0, 1]])

    # Plot
    plt.figure()
    plt.plot(MEAN[0], MEAN[1], "+", color="green")
    draw_cov_ellipse(MEAN, SIGMA)
    plt.plot(mmm[0], mmm[1], "+", color="green")
    draw_cov_ellipse(mmm, sss)
    plt.plot(MEAN[0]*4, MEAN[1]*4, "+", color="green")
    draw_cov_ellipse(np.array(MEAN)*4, SIGMA*0.5)
    plt.show()
    print("Probability: ", p_multivariate_normal([1, 1], MEAN, SIGMA))
