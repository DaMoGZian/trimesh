// load a scene saved as base64 encoded GLTF/GLB
var camera, controls, scene, renderer, tracklight;

// Fit the camera to an object's bounding sphere
function autoFitTo(obj, camera, controls) {
  // oriented bounding box
  const boundingBox = new THREE.Box3().setFromObject(obj);
  // get the bounding sphere of the OBB
  const boundingSphere = new THREE.Sphere();
  boundingBox.getBoundingSphere((target = boundingSphere));

  // object size / display size
  const scale = 1.0;
  // convert to radians and scale
  const angularSize = camera.fov * Math.PI / 180 * scale;

  const distanceToCamera = boundingSphere.radius / Math.tan(angularSize);
  const len = Math.sqrt(
    Math.pow(distanceToCamera, 2) +
      Math.pow(distanceToCamera, 2) +
      Math.pow(distanceToCamera, 2)
  );

  camera.position.set(len, len, len);

  controls.update();

  camera.lookAt(boundingSphere.center);
  controls.target.set(
    boundingSphere.center.x,
    boundingSphere.center.y,
    boundingSphere.center.z
  );
  camera.updateProjectionMatrix();
}

function init() {
  camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.01,
    1000
  );

  controls = new THREE.TrackballControls(camera);
  controls.rotateSpeed = 1.0;
  controls.zoomSpeed = 1.2;
  controls.panSpeed = 0.8;
  controls.noZoom = false;
  controls.noPan = false;
  controls.staticMoving = true;
  controls.dynamicDampingFactor = 0.3;
  controls.keys = [65, 83, 68];
  controls.addEventListener("change", render);

  scene = new THREE.Scene();
  // white background
  scene.background = new THREE.Color(0xffffff);

  // add a light that will track the camera
  tracklight = new THREE.DirectionalLight(0xffffff, 1.75);
  scene.add(tracklight);

  // base64 encoded GLTF (GLB) scene
  base64_data =
    "Z2xURgIAAAAcBAAAEAMAAEpTT057ImFjY2Vzc29ycyI6IFt7Im1pbiI6IFswXSwgInR5cGUiOiAiU0NBTEFSIiwgImNvdW50IjogMzYsICJidWZmZXJWaWV3IjogMCwgImNvbXBvbmVudFR5cGUiOiA1MTI1LCAibWF4IjogWzddfSwgeyJtaW4iOiBbLTAuNSwgLTAuNSwgLTAuNV0sICJ0eXBlIjogIlZFQzMiLCAiY291bnQiOiA4LCAiYnVmZmVyVmlldyI6IDEsICJjb21wb25lbnRUeXBlIjogNTEyNiwgIm1heCI6IFswLjUsIDAuNSwgMC41XX1dLCAiYXNzZXQiOiB7ImdlbmVyYXRvciI6ICJnaXRodWIuY29tL21pa2VkaC90cmltZXNoIiwgInZlcnNpb24iOiAiMi4wIn0sICJub2RlcyI6IFt7ImNoaWxkcmVuIjogWzFdLCAibmFtZSI6ICJ3b3JsZCJ9LCB7Im1hdHJpeCI6IFsxLjAsIDAuMCwgMC4wLCAwLjAsIDAuMCwgMS4wLCAwLjAsIDAuMCwgMC4wLCAwLjAsIDEuMCwgMC4wLCAwLjAsIDAuMCwgMC4wLCAxLjBdLCAibmFtZSI6ICJnZW9tZXRyeV8wXzAiLCAibWVzaCI6IDB9XSwgInNjZW5lcyI6IFt7Im5vZGVzIjogWzBdfV0sICJzY2VuZSI6IDAsICJidWZmZXJWaWV3cyI6IFt7ImJ1ZmZlciI6IDAsICJieXRlTGVuZ3RoIjogMTQ0LCAiYnl0ZU9mZnNldCI6IDB9LCB7ImJ1ZmZlciI6IDAsICJieXRlTGVuZ3RoIjogOTYsICJieXRlT2Zmc2V0IjogMTQ0fV0sICJidWZmZXJzIjogW3siYnl0ZUxlbmd0aCI6IDI0MH1dLCAibWVzaGVzIjogW3sicHJpbWl0aXZlcyI6IFt7ImF0dHJpYnV0ZXMiOiB7IlBPU0lUSU9OIjogMX0sICJpbmRpY2VzIjogMCwgIm1vZGUiOiA0fV0sICJuYW1lIjogImdlb21ldHJ5XzAifV198AAAAEJJTgABAAAAAwAAAAAAAAAEAAAAAQAAAAAAAAAAAAAAAwAAAAIAAAACAAAABAAAAAAAAAABAAAABwAAAAMAAAAFAAAAAQAAAAQAAAAFAAAABwAAAAEAAAADAAAABwAAAAIAAAAGAAAABAAAAAIAAAACAAAABwAAAAYAAAAGAAAABQAAAAQAAAAHAAAABQAAAAYAAAAAAAC/AAAAvwAAAL8AAAC/AAAAvwAAAD8AAAC/AAAAPwAAAL8AAAC/AAAAPwAAAD8AAAA/AAAAvwAAAL8AAAA/AAAAvwAAAD8AAAA/AAAAPwAAAL8AAAA/AAAAPwAAAD8=";

  // renderer
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);
  document.body.appendChild(renderer.domElement);

  // load GLTF data from base64 string
  loader = new THREE.GLTFLoader();
  loader.load(
    "data:text/plain;base64," + base64_data,
    // function will be called asynchronously after data is loaded
    function(gltf) {
      // add GLTF data to scene
      scene.add(gltf.scene);
      // after loading fit camera to scene
      autoFitTo(scene, camera, controls);
      // render
      render();
    }
  );

  window.addEventListener("resize", onWindowResize, false);

  // enable controls
  animate();
}

function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  controls.handleResize();
  render();
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();
}

function render() {
  // we always want things lit for our preview window
  tracklight.position.copy(camera.position);
  renderer.render(scene, camera);
}

init();
