trimesh.io
============

Mesh importers and exporters.


## Tips for New Importers/Exporters/Code

Python can be fast, but only when you use it as little as possible. In general, if you ever have a block which loops through faces and vertices it will be basically unusable with even moderately sized meshes. All operations on face or vertex arrays should be vectorized numpy operations unless absolutely unavoidable. Profiling helps figure out what is slow, but some general advice:

### Do
- Run your test script with `ipython -i newstuff.py` and profile with magic, i.e. `%timeit var.split()`
- Use `np.fromstring`, `np.frombuffer`
- Use `str.split` or `np.fromstring`:
```
In [6]: %timeit np.array(text.split(), dtype=np.float64)
1000 loops, best of 3: 209 µs per loop

In [7]: %timeit np.fromstring(text, sep='\n', dtype=np.float64)
10000 loops, best of 3: 139 µs per loop
```
- Use giant format strings rather than looping, appending, or even iterator joining:
```
In [14]: array = np.random.random((10000,3))

In [15]: %timeit '\n'.join('{}/{}/{}'.format(*row) for row in array)
10 loops, best of 3: 60.3 ms per loop

In [16]: %timeit ('{}/{}/{}\n' * len(array))[:-1].format(*array.flatten())
10 loops, best of 3: 34.3 ms per loop
```
- Sometimes you can use sparse matrices to replace a loop and get a huge speedup. [Here's the same algorithm implemented two ways, looping and sparse dot products.](https://github.com/mikedh/trimesh/blob/master/trimesh/geometry.py#L186-L203)


### Don't
- Loop through potentially giant arrays


### Dependencies
The highest priority is making sure `pip install trimesh` basically always works. If someone just wants an STL loader they shouldn't need to compile 8 million things and install half of pypi. Also in general all dependencies should be running unit tests in CI on Python 2.7 and 3.4-3.7 on Windows and Linux (OSX as a bonus). 

#### `pip install trimesh[easy]` 
Install things that install cleanly on all major platforms / Python versions without compiling (they have working wheels). Unfortunately two packages (`rtree` and `shapely`) currently required additional shared libraries to function rather than including them in the wheels.

#### `pip install trimesh[all]`
Includes libraries that need compiling. Should be able to install through some means on all platforms.