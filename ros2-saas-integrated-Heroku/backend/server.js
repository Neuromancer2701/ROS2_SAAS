// Simple Node.js Express server placeholder for Heroku deployment

const express = require('express');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000; // Heroku sets PORT env variable

app.use(express.json()); // Middleware to parse JSON bodies
app.use(express.static(path.join(__dirname, '../src_projects/ros2-front-end'))); // Serve static files from ros2-front-end

// Basic route
app.get('/', (req, res) => {
  // Serve the index.html from ros2-front-end
  res.sendFile(path.join(__dirname, '../src_projects/ros2-front-end/index.html'));
});

app.get('/api/status', (req, res) => {
  res.json({ status: 'Node.js backend is running', ros_api_status: 'not_checked' });
});

// Endpoint to interact with the Python ROS operations script
app.post('/api/ros', (req, res) => {
  const { command, args } = req.body; // Expecting command and arguments for the Python script

  if (!command) {
    return res.status(400).json({ error: 'Missing "command" in request body' });
  }

  const pythonScriptPath = path.join(__dirname, '../ros_operations_api.py');
  const scriptArgs = [pythonScriptPath, command, ...(args || [])];

  console.log(`Executing Python script: python3 ${scriptArgs.join(' ')}`);

  const pythonProcess = spawn('python3', scriptArgs);

  let stdoutData = '';
  let stderrData = '';

  pythonProcess.stdout.on('data', (data) => {
    stdoutData += data.toString();
    console.log(`Python stdout: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    stderrData += data.toString();
    console.error(`Python stderr: ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python script exited with code ${code}`);
    if (code === 0) {
      try {
        // Try to parse stdout as JSON, otherwise return as text
        const jsonData = JSON.parse(stdoutData);
        res.json({ success: true, output: jsonData, exit_code: code });
      } catch (e) {
        res.json({ success: true, output: stdoutData.trim(), exit_code: code });
      }
    } else {
      res.status(500).json({ success: false, error: stderrData.trim() || "Python script failed", output: stdoutData.trim(), exit_code: code });
    }
  });

  pythonProcess.on('error', (err) => {
    console.error('Failed to start Python subprocess.', err);
    res.status(500).json({ success: false, error: 'Failed to start Python subprocess.', details: err.message });
  });
});


// --- Placeholder for ROS Actions from `ros2-package-generator` ---
// This demonstrates how the Node.js backend could invoke the package generator.
// The actual `ros_operations_api.py` would handle the logic.
app.post('/api/generate-package', (req, res) => {
  const { language, package_name, node_type, options } = req.body;

  if (!language || !package_name || !node_type) {
    return res.status(400).json({ error: "Missing required fields: language, package_name, node_type" });
  }

  // Construct arguments for ros2_pkg_gen.py
  // This path assumes ros2_package_generator is accessible where python script runs
  const generatorScriptPath = path.join(__dirname, '../src_projects/ros2-package-generator/src/ros2_pkg_gen.py');

  let scriptArgs = [
    generatorScriptPath,
    language,
    package_name,
    node_type
  ];

  if (options) {
    if (options.node_name) scriptArgs.push('--node-name', options.node_name);
    if (options.topic_name) scriptArgs.push('--topic-name', options.topic_name);
    if (options.service_name) scriptArgs.push('--service-name', options.service_name);
    if (options.action_name) scriptArgs.push('--action-name', options.action_name);
    // Add other options as needed
    // Target path for generated package would be tricky in Heroku's ephemeral FS.
    // This would likely generate into a temporary location or a mounted volume if available.
    // For Heroku, generated code might need to be sent back to user or stored in DB/cloud storage.
    scriptArgs.push('--target-path', '/tmp/generated_pkgs'); // Example temporary path
  }

  console.log(`Executing package generator: python3 ${scriptArgs.join(' ')}`);
  const pythonProcess = spawn('python3', scriptArgs);

  let stdoutData = '';
  let stderrData = '';
  pythonProcess.stdout.on('data', (data) => { stdoutData += data.toString(); console.log(`PkgGen stdout: ${data}`); });
  pythonProcess.stderr.on('data', (data) => { stderrData += data.toString(); console.error(`PkgGen stderr: ${data}`); });

  pythonProcess.on('close', (code) => {
    if (code === 0) {
      res.json({
        success: true,
        message: `Package ${package_name} generation script executed. Output path (simulated): /tmp/generated_pkgs/${package_name}`,
        details: stdoutData.trim()
      });
    } else {
      res.status(500).json({ success: false, error: `Package generation failed. Exit code: ${code}`, details: stderrData.trim() });
    }
  });
   pythonProcess.on('error', (err) => {
    console.error('Failed to start package generator subprocess.', err);
    res.status(500).json({ success: false, error: 'Failed to start package generator subprocess.', details: err.message });
  });
});


app.listen(PORT, () => {
  console.log(`Node.js backend server listening on port ${PORT}`);
  console.log(`Serving frontend from: ${path.join(__dirname, '../src_projects/ros2-front-end')}`);
});

// Basic error handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send('Something broke!');
});
```

This `server.js` now includes:
1.  Basic Express setup.
2.  Serving of static files from `src_projects/ros2-front-end` (specifically `index.html` at the root).
3.  A `/api/status` endpoint.
4.  A `/api/ros` endpoint that uses `child_process.spawn` to execute the `ros_operations_api.py` script. This is a common way for Node.js to interact with Python scripts.
5.  A placeholder `/api/generate-package` endpoint showing how it might call the `ros2_pkg_gen.py` script.

The `Dockerfile` and `package.json` are already designed to support this structure. The next step will be to create `ros_operations_api.py`.
