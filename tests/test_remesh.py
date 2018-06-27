try:
    from . import generic as g
except BaseException:
    import generic as g


class SubDivideTest(g.unittest.TestCase):

    def test_subdivide(self):
        meshes = [g.get_mesh('soup.stl'),  # a soup of random triangles
                  g.get_mesh('cycloidal.ply'),  # a mesh with multiple bodies
                  g.get_mesh('featuretype.STL')]  # a mesh with a single body

        for m in meshes:
            sub = m.subdivide()
            assert g.np.allclose(m.area, sub.area)
            assert len(sub.faces) > len(m.faces)

            v, f = g.trimesh.remesh.subdivide(vertices=m.vertices,
                                              faces=m.faces)

            max_edge = m.scale / 50
            v, f = g.trimesh.remesh.subdivide_to_size(vertices=m.vertices,
                                                      faces=m.faces,
                                                      max_edge=max_edge)
            ms = g.trimesh.Trimesh(vertices=v, faces=f)

            assert g.np.allclose(m.area, ms.area)

            edge_len = (g.np.diff(ms.vertices[ms.edges_unique],
                                  axis=1).reshape((-1, 3))**2).sum(axis=1)**.5

            assert (edge_len < max_edge).all()


if __name__ == '__main__':
    g.trimesh.util.attach_to_log()
    g.unittest.main()
