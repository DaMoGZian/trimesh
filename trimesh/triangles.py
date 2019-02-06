"""
triangles.py
-------------

Functions for dealing with triangle soups in (n, 3, 3) float form.
"""
import numpy as np

from . import util

from .points import point_plane_distance
from .constants import tol


def cross(triangles):
    """
    Returns the cross product of two edges from input triangles

    Parameters
    --------------
    triangles: (n, 3, 3) float, vertices of triangles

    Returns
    --------------
    crosses: (n, 3) float, cross product of two edge vectors
    """
    vectors = np.diff(triangles, axis=1)
    crosses = np.cross(vectors[:, 0], vectors[:, 1])
    return crosses


def area(triangles=None, crosses=None, sum=False):
    """
    Calculates the sum area of input triangles

    Parameters
    ----------
    triangles: vertices of triangles (n,3,3)
    sum:       bool, return summed area or individual triangle area

    Returns
    ----------
    area:
        if sum: float, sum area of triangles
        else:   (n,) float, individual area of triangles
    """
    if crosses is None:
        crosses = cross(triangles)
    area = (np.sum(crosses**2, axis=1)**.5) * .5
    if sum:
        return np.sum(area)
    return area


def normals(triangles=None, crosses=None):
    """
    Calculates the normals of input triangles

    Parameters
    ------------
    triangles:   (n, 3, 3) float, vertex positions
    crosses:     (n, 3) float, cross products of edge vectors

    Returns
    ------------
    normals: (m, 3) float, normal vectors
    valid:   (n,)   bool, valid
    """
    if crosses is None:
        crosses = cross(triangles)
    # unitize the cross product vectors
    unit, valid = util.unitize(crosses, check_valid=True)
    return unit, valid


def angles(triangles):
    """
    Calculates the angles of input triangles

    Parameters
    ------------
    triangles:   (n, 3, 3) float, vertex positions

    Returns
    ------------
    angles: (n, 3) float, angles at vertex positions (radian)
    """
    ABCs = util.unitize((triangles - np.roll(triangles, -1, axis=1)).reshape(-1,3))
    inner1d = lambda us, vs: np.einsum('...i,...i', us, vs)
    return np.arccos([inner1d(ABCs[::3], -ABCs[2::3]),      # AB o AC
                      inner1d(-ABCs[::3], ABCs[1::3]),      # BA o BC
                      inner1d(ABCs[2::3], -ABCs[1::3])]).T  # CA o CB


def all_coplanar(triangles):
    """
    Check to see if a list of triangles are all coplanar

    Parameters
    ----------------
    triangles: (n, 3, 3) float, vertices of triangles

    Returns
    ---------------
    all_coplanar, bool, True if all triangles are coplanar
    """
    triangles = np.asanyarray(triangles, dtype=np.float64)
    if not util.is_shape(triangles, (-1, 3, 3)):
        raise ValueError('Triangles must be (n,3,3)!')

    test_normal = normals(triangles)[0]
    test_vertex = triangles[0][0]
    distances = point_plane_distance(points=triangles[1:].reshape((-1, 3)),
                                     plane_normal=test_normal,
                                     plane_origin=test_vertex)
    all_coplanar = np.all(np.abs(distances) < tol.zero)
    return all_coplanar


def any_coplanar(triangles):
    """
    Given a list of triangles, if the FIRST triangle is coplanar with ANY
    of the following triangles, return True.
    Otherwise, return False.
    """
    triangles = np.asanyarray(triangles, dtype=np.float64)
    if not util.is_shape(triangles, (-1, 3, 3)):
        raise ValueError('Triangles must be (n,3,3)!')

    test_normal = normals(triangles)[0]
    test_vertex = triangles[0][0]
    distances = point_plane_distance(points=triangles[1:].reshape((-1, 3)),
                                     plane_normal=test_normal,
                                     plane_origin=test_vertex)
    any_coplanar = np.any(
        np.all(np.abs(distances.reshape((-1, 3)) < tol.zero), axis=1))
    return any_coplanar


def mass_properties(triangles,
                    crosses=None,
                    density=1.0,
                    center_mass=None,
                    skip_inertia=False):
    """
    Calculate the mass properties of a group of triangles.

    Implemented from:
    http://www.geometrictools.com/Documentation/PolyhedralMassProperties.pdf

    Parameters
    ----------
    triangles:    (n,3,3) float, triangles in space
    crosses:      (n,) float, cross products of triangles
    density:      float, optional override for density
    center_mass:  (3,) float, optional override for center mass
    skip_inertia: bool, if True will not return moments matrix

    Returns
    ---------
    info: dict, mass properties
    """
    triangles = np.asanyarray(triangles, dtype=np.float64)
    if not util.is_shape(triangles, (-1, 3, 3)):
        raise ValueError('Triangles must be (n,3,3)!')

    if crosses is None:
        crosses = cross(triangles)

    # these are the subexpressions of the integral
    f1 = triangles.sum(axis=1)

    # for the the first vertex of every triangle:
    # triangles[:,0,:] will give rows like [[x0, y0, z0], ...]

    # for the x coordinates of every triangle
    # triangles[:,:,0] will give rows like [[x0, x1, x2], ...]
    f2 = (triangles[:, 0, :]**2 +
          triangles[:, 1, :]**2 +
          triangles[:, 0, :] * triangles[:, 1, :] +
          triangles[:, 2, :] * f1)
    f3 = ((triangles[:, 0, :]**3) +
          (triangles[:, 0, :]**2) * (triangles[:, 1, :]) +
          (triangles[:, 0, :]) * (triangles[:, 1, :]**2) +
          (triangles[:, 1, :]**3) +
          (triangles[:, 2, :] * f2))
    g0 = (f2 + (triangles[:, 0, :] + f1) * triangles[:, 0, :])
    g1 = (f2 + (triangles[:, 1, :] + f1) * triangles[:, 1, :])
    g2 = (f2 + (triangles[:, 2, :] + f1) * triangles[:, 2, :])
    integral = np.zeros((10, len(f1)))
    integral[0] = crosses[:, 0] * f1[:, 0]
    integral[1:4] = (crosses * f2).T
    integral[4:7] = (crosses * f3).T
    for i in range(3):
        triangle_i = np.mod(i + 1, 3)
        integral[i + 7] = crosses[:, i] * ((triangles[:, 0, triangle_i] * g0[:, i]) +
                                           (triangles[:, 1, triangle_i] * g1[:, i]) +
                                           (triangles[:, 2, triangle_i] * g2[:, i]))

    coefficients = 1.0 / np.array([6, 24, 24, 24, 60, 60, 60, 120, 120, 120],
                                  dtype=np.float64)
    integrated = integral.sum(axis=1) * coefficients

    volume = integrated[0]

    if center_mass is None:
        if np.abs(volume) < tol.zero:
            center_mass = np.zeros(3)
        else:
            center_mass = integrated[1:4] / volume

    mass = density * volume

    result = {'density': density,
              'mass': mass,
              'volume': volume,
              'center_mass': center_mass}

    if skip_inertia:
        return result

    inertia = np.zeros((3, 3))
    inertia[0, 0] = integrated[5] + integrated[6] - \
        (volume * (center_mass[[1, 2]]**2).sum())
    inertia[1, 1] = integrated[4] + integrated[6] - \
        (volume * (center_mass[[0, 2]]**2).sum())
    inertia[2, 2] = integrated[4] + integrated[5] - \
        (volume * (center_mass[[0, 1]]**2).sum())
    inertia[0, 1] = (
        integrated[7] - (volume * np.product(center_mass[[0, 1]])))
    inertia[1, 2] = (
        integrated[8] - (volume * np.product(center_mass[[1, 2]])))
    inertia[0, 2] = (
        integrated[9] - (volume * np.product(center_mass[[0, 2]])))
    inertia[2, 0] = inertia[0, 2]
    inertia[2, 1] = inertia[1, 2]
    inertia[1, 0] = inertia[0, 1]
    inertia *= density
    result['inertia'] = inertia

    return result


def windings_aligned(triangles, normals_compare):
    """
    Given a list of triangles and a list of normals determine if the
    two are aligned

    Parameters
    ----------
    triangles: (n,3,3) list of vertex locations
    normals_compare: (n,3) list of normals

    Returns
    ----------
    aligned: (n) bool list, are normals aligned with triangles
    """
    triangles = np.asanyarray(triangles, dtype=np.float64)
    if not util.is_shape(triangles, (-1, 3, 3)):
        raise ValueError('Triangles must be (n,3,3)!')

    calculated, valid = normals(triangles)
    difference = util.diagonal_dot(calculated,
                                   normals_compare[valid])

    aligned = np.zeros(len(triangles), dtype=np.bool)
    aligned[valid] = difference > 0.0

    return aligned


def bounds_tree(triangles):
    """
    Given a list of triangles, create an r-tree for broad- phase
    collision detection

    Parameters
    ---------
    triangles: (n, 3, 3) list of vertices

    Returns
    ---------
    tree: Rtree object
    """
    triangles = np.asanyarray(triangles, dtype=np.float64)
    if not util.is_shape(triangles, (-1, 3, 3)):
        raise ValueError('Triangles must be (n,3,3)!')

    # the (n,6) interleaved bounding box for every triangle
    triangle_bounds = np.column_stack((triangles.min(axis=1),
                                       triangles.max(axis=1)))
    tree = util.bounds_tree(triangle_bounds)
    return tree


def nondegenerate(triangles, areas=None, height=None):
    """
    Find all triangles which have an oriented bounding box
    where both of the two sides is larger than a specified height.

    Degenerate triangles can be when:
    1) Two of the three vertices are colocated
    2) All three vertices are unique but colinear


    Parameters
    ----------
    triangles: (n, 3, 3) float, list of triangles
    height:    float, minimum edge of a triangle to be kept

    Returns
    ----------
    nondegenerate: (n,) bool array of triangles that have area
    """
    triangles = np.asanyarray(triangles, dtype=np.float64)
    if not util.is_shape(triangles, (-1, 3, 3)):
        raise ValueError('Triangles must be (n,3,3)!')

    if height is None:
        height = tol.merge

    # if both edges of the triangles OBB are longer than tol.merge
    # we declare them to be nondegenerate
    ok = (extents(triangles=triangles,
                  areas=areas) > height).all(axis=1)

    return ok


def extents(triangles, areas=None):
    """
    Return the 2D bounding box size of each triangle.


    Parameters
    ----------
    triangles: (n, 3, 3) float, list of triangles
    areas:     (n,) float,      list of triangles area


    Returns
    ----------
    box:       (n,2) float, the size of the 2D oriented bounding box.
    """
    triangles = np.asanyarray(triangles, dtype=np.float64)
    if not util.is_shape(triangles, (-1, 3, 3)):
        raise ValueError('Triangles must be (n,3,3)!')

    if areas is None:
        areas = area(triangles=triangles,
                     sum=False)

    # the edge vectors which define the triangle
    a = triangles[:, 1] - triangles[:, 0]
    b = triangles[:, 2] - triangles[:, 0]

    # length of the edge vectors
    length_a = (a**2).sum(axis=1)**.5
    length_b = (b**2).sum(axis=1)**.5

    # which edges are acceptable length
    nonzero_a = length_a > tol.merge
    nonzero_b = length_b > tol.merge

    # find the two heights of the triangle
    # essentially this is the side length of an
    # oriented bounding box, per triangle
    box = np.zeros((len(triangles), 2), dtype=np.float64)
    box[:, 0][nonzero_a] = (areas[nonzero_a] * 2) / length_a[nonzero_a]
    box[:, 1][nonzero_b] = (areas[nonzero_b] * 2) / length_b[nonzero_b]

    return box


def barycentric_to_points(triangles, barycentric):
    """
    Convert a list of barycentric coordinates on a list of triangles
    to cartesian points.

    Parameters
    ----------
    triangles:   (n,3,3) float, list of triangles in space
    barycentric: (n,2) float, barycentric coordinates

    Returns
    -----------
    points: (m,3) float, points in space
    """
    barycentric = np.asanyarray(barycentric, dtype=np.float64)
    triangles = np.asanyarray(triangles, dtype=np.float64)

    if not util.is_shape(triangles, (-1, 3, 3)):
        raise ValueError('Triangles must be (n,3,3)!')
    if barycentric.shape == (2,):
        barycentric = np.ones((len(triangles), 2),
                              dtype=np.float64) * barycentric
    if util.is_shape(barycentric, (len(triangles), 2)):
        barycentric = np.column_stack((barycentric,
                                       1.0 - barycentric.sum(axis=1)))
    elif not util.is_shape(barycentric, (len(triangles), 3)):
        raise ValueError('Barycentric shape incorrect!')

    barycentric /= barycentric.sum(axis=1).reshape((-1, 1))
    points = (triangles * barycentric.reshape((-1, 3, 1))).sum(axis=1)

    return points


def points_to_barycentric(triangles, points, method='cramer'):
    """
    Find the barycentric coordinates of points relative to triangles.

    The Cramer's rule solution implements:
        http://blackpawn.com/texts/pointinpoly

    The cross product solution implements:
        https://www.cs.ubc.ca/~heidrich/Papers/JGT.05.pdf


    Parameters
    -----------
    triangles: (n,3,3) float, triangles in space
    points:    (n,3) float, point in space associated with a triangle
    method:    str, which method to compute the barycentric coordinates with. Options:
               -'cross': uses a method using cross products, roughly 2x slower but
                         different numerical robustness properties
               -anything else: uses a cramer's rule solution

    Returns
    -----------
    barycentric: (n,3) float, barycentric
    """

    def method_cross():
        n = np.cross(edge_vectors[:, 0], edge_vectors[:, 1])
        denominator = util.diagonal_dot(n, n)

        barycentric = np.zeros((len(triangles), 3), dtype=np.float64)
        barycentric[:, 2] = util.diagonal_dot(
            np.cross(edge_vectors[:, 0], w), n) / denominator
        barycentric[:, 1] = util.diagonal_dot(
            np.cross(w, edge_vectors[:, 1]), n) / denominator
        barycentric[:, 0] = 1 - barycentric[:, 1] - barycentric[:, 2]
        return barycentric

    def method_cramer():
        dot00 = util.diagonal_dot(edge_vectors[:, 0], edge_vectors[:, 0])
        dot01 = util.diagonal_dot(edge_vectors[:, 0], edge_vectors[:, 1])
        dot02 = util.diagonal_dot(edge_vectors[:, 0], w)
        dot11 = util.diagonal_dot(edge_vectors[:, 1], edge_vectors[:, 1])
        dot12 = util.diagonal_dot(edge_vectors[:, 1], w)

        inverse_denominator = 1.0 / (dot00 * dot11 - dot01 * dot01)

        barycentric = np.zeros((len(triangles), 3), dtype=np.float64)
        barycentric[:, 2] = (dot00 * dot12 - dot01 *
                             dot02) * inverse_denominator
        barycentric[:, 1] = (dot11 * dot02 - dot01 *
                             dot12) * inverse_denominator
        barycentric[:, 0] = 1 - barycentric[:, 1] - barycentric[:, 2]
        return barycentric

    # establish that input triangles and points are sane
    triangles = np.asanyarray(triangles, dtype=np.float64)
    points = np.asanyarray(points, dtype=np.float64)
    if not util.is_shape(triangles, (-1, 3, 3)):
        raise ValueError('triangles shape incorrect')
    if not util.is_shape(points, (len(triangles), 3)):
        raise ValueError('triangles and points must correspond')

    edge_vectors = triangles[:, 1:] - triangles[:, :1]
    w = points - triangles[:, 0].reshape((-1, 3))

    if method == 'cross':
        return method_cross()
    return method_cramer()


def closest_point(ABCs, Ds, returnDists = False):
    #from numpy.core.umath_tests import inner1d # fast but deprecated in future numpy versions
    inner1d = lambda u, v: (u * v).sum(axis=1)
    simpleCross = lambda a, b: np.array([a[:,1]*b[:,2]-a[:,2]*b[:,1],a[:,2]*b[:,0]-a[:,0]*b[:,2],a[:,0]*b[:,1]-a[:,1]*b[:,0]]).T

    closestPts = np.empty_like(Ds)

    # edge vectors AB, BC, CA
    eVecsABC = ABCs[:,[1,2,0]] - ABCs

    # normals of all triangles
    normalsABC = simpleCross(eVecsABC[:,0], eVecsABC[:,1])
    normalsABC /= np.sqrt(np.sum(normalsABC**2,axis=1)).reshape(-1,1)

    # project points into triangle planes
    distsToPlanes = inner1d(ABCs[:,0] - Ds, normalsABC)
    DsInPlane = Ds + normalsABC * distsToPlanes.reshape(-1,1)

    # (in plane) vectors from each ABC vertex to the projected points
    inPlaneVecs = np.repeat(DsInPlane.reshape(-1,1,3), 3, axis=1) - ABCs

    # by the right-hand rule: edge-vectors (index finger) x normal (middle finger)
    # compute the r-vectors (thumb) pointing away from the triangle
    rVecsABC = simpleCross(eVecsABC.reshape(-1,3), np.repeat(normalsABC, 3, axis=0))
    distsToEdgeLines = inner1d(rVecsABC, inPlaneVecs.reshape(-1,3)).reshape(-1,3)

    # separate points on the inside/outside of the triange with the dot-product signs
    case_inside = np.all(distsToEdgeLines <= 0, axis=1)
    case_outside = True ^ case_inside

    # distances and points of in-triangle projections are already there
    closestPts[case_inside] = DsInPlane[case_inside]

    # with the max. positive to-edge-distance we select vertex U of the triangle,
    # the corresponding edge from U to V, and vector from U to the projection of D
    # https://ggbm.at/qfxsevaq    
    vIdxs = np.argmax(distsToEdgeLines[case_outside], axis=1)
    uvVecs = eVecsABC[case_outside, vIdxs]
    udVecs = inPlaneVecs[case_outside, vIdxs]

    # the closest point is on the line of U and V but clipped to the edge's extent
    UtoVscale = np.clip(inner1d(udVecs, uvVecs) / inner1d(uvVecs, uvVecs), 0, 1)

    # compute the closest points on edge UV
    closestPts[case_outside] = ABCs[case_outside,vIdxs] + uvVecs * UtoVscale.reshape(-1,1)

    # we can recycle some distances if required
    if returnDists:
        closestDists = np.empty(len(Ds), np.float32)
        closestDists[case_inside] = np.abs(distsToPlanes[case_inside])
        closestDists[case_outside] = np.sqrt(np.sum((Ds[case_outside] - closestPts[case_outside])**2, axis=1))
        return closestDists

    return closestPts


def to_kwargs(triangles):
    """
    Convert a list of triangles to the kwargs for the Trimesh constructor.

    Parameters
    ---------
    triangles: (n,3,3) float, triangles in space

    Returns
    ---------
    kwargs: dict, with keys:
                   'vertices' : (n,3) float
                   'faces'    : (m,3) int

    Examples
    ---------
    mesh = trimesh.Trimesh(**trimesh.triangles.to_kwargs(triangles))
    """
    triangles = np.asanyarray(triangles, dtype=np.float64)
    if not util.is_shape(triangles, (-1, 3, 3)):
        raise ValueError('Triangles must be (n,3,3)!')

    vertices = triangles.reshape((-1, 3))
    faces = np.arange(len(vertices)).reshape((-1, 3))
    kwargs = {'vertices': vertices,
              'faces': faces}

    return kwargs
