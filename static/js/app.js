// SmartAttendAI JavaScript
class SmartAttendAI {
  constructor() {
    this.video = document.getElementById("video");
    this.canvas = document.getElementById("canvas");
    this.status = document.getElementById("status");
    this.stream = null;

    this.initializeEventListeners();
  }

  initializeEventListeners() {
    document.getElementById("start-camera").addEventListener("click", () => {
      this.startCamera();
    });

    document.getElementById("take-attendance").addEventListener("click", () => {
      this.takeAttendance();
    });

    document
      .getElementById("register-student")
      .addEventListener("click", () => {
        this.registerStudent();
      });
  }

  async startCamera() {
    try {
      this.updateStatus("Starting camera...");

      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
      });

      this.video.srcObject = this.stream;
      this.updateStatus("Camera ready! Position your face in the frame.");
    } catch (error) {
      console.error("Error accessing camera:", error);
      this.updateStatus(
        "Error: Could not access camera. Please check permissions.",
      );
    }
  }

  async takeAttendance() {
    if (!this.stream) {
      this.updateStatus("Please start camera first");
      return;
    }

    this.updateStatus("Processing attendance...");

    // Capture frame from video
    const context = this.canvas.getContext("2d");
    this.canvas.width = this.video.videoWidth;
    this.canvas.height = this.video.videoHeight;
    context.drawImage(this.video, 0, 0);

    // Convert to base64
    const imageData = this.canvas.toDataURL("image/jpeg");

    try {
      // Send to backend for processing
      const response = await fetch("/api/attendance", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          image: imageData,
          timestamp: new Date().toISOString(),
        }),
      });

      const result = await response.json();

      if (result.success) {
        this.updateStatus(`Attendance marked for ${result.student_name}`);
      } else {
        this.updateStatus("Attendance failed: " + result.message);
      }
    } catch (error) {
      console.error("Error processing attendance:", error);
      this.updateStatus("Error processing attendance. Please try again.");
    }
  }

  async registerStudent() {
    const name = prompt("Enter student name:");
    const studentId = prompt("Enter student ID:");

    if (!name || !studentId) {
      this.updateStatus("Registration cancelled");
      return;
    }

    if (!this.stream) {
      this.updateStatus("Please start camera first");
      return;
    }

    this.updateStatus("Capturing student photo...");

    // Capture frame from video
    const context = this.canvas.getContext("2d");
    this.canvas.width = this.video.videoWidth;
    this.canvas.height = this.video.videoHeight;
    context.drawImage(this.video, 0, 0);

    // Convert to base64
    const imageData = this.canvas.toDataURL("image/jpeg");

    try {
      // Send to backend for registration
      const response = await fetch("/api/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: name,
          student_id: studentId,
          image: imageData,
        }),
      });

      const result = await response.json();

      if (result.success) {
        this.updateStatus(`Student ${name} registered successfully!`);
      } else {
        this.updateStatus("Registration failed: " + result.message);
      }
    } catch (error) {
      console.error("Error registering student:", error);
      this.updateStatus("Error registering student. Please try again.");
    }
  }

  updateStatus(message) {
    this.status.textContent = message;
    console.log("Status:", message);
  }
}

// Initialize the application when page loads
document.addEventListener("DOMContentLoaded", () => {
  new SmartAttendAI();
});
