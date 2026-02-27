/**
 * SmartAttendAI - Comprehensive Attendance System
 * Includes GPS validation, face recognition, and liveness detection
 */

class AttendanceVerificationSystem {
  constructor() {
    this.video = document.getElementById("video");
    this.canvas = document.getElementById("canvas");
    this.statusArea = document.getElementById("status-area");
    this.stream = null;
    this.isProcessing = false;
    this.recordedFrames = [];
    this.recordingStartTime = null;

    // Verification state
    this.verificationData = {
      studentId: null,
      classroom: null,
      latitude: null,
      longitude: null,
      accuracy: null,
      faceImage: null,
      videoFrames: [],
      challengeType: null,
      challengeFrames: [],
    };

    this.currentStep = 0;
    this.steps = [
      "Select Student",
      "GPS Validation",
      "Face Capture",
      "Liveness Check",
      "Challenge-Response",
      "Mark Attendance",
    ];

    this.initializeEventListeners();
    this.updateProgressBar();
  }

  initializeEventListeners() {
    // Camera controls
    document
      .getElementById("start-camera-btn")
      ?.addEventListener("click", () => this.startCamera());
    document
      .getElementById("stop-camera-btn")
      ?.addEventListener("click", () => this.stopCamera());
    document
      .getElementById("capture-face-btn")
      ?.addEventListener("click", () => this.captureFaceImage());
    document
      .getElementById("start-liveness-btn")
      ?.addEventListener("click", () => this.startLivenessDetection());
    document
      .getElementById("start-challenge-btn")
      ?.addEventListener("click", () => this.startChallengeVerification());
    document
      .getElementById("submit-attendance-btn")
      ?.addEventListener("click", () => this.submitAttendance());

    // Student selection
    document
      .getElementById("student-select")
      ?.addEventListener("change", (e) => {
        this.verificationData.studentId = e.target.value;
      });

    document
      .getElementById("classroom-select")
      ?.addEventListener("change", (e) => {
        this.verificationData.classroom = e.target.value;
      });

    // Get GPS location
    document
      .getElementById("get-gps-btn")
      ?.addEventListener("click", () => this.getGPSLocation());
  }

  // ============ STEP 1: Student Selection & GPS Validation ============

  async getGPSLocation() {
    this.updateStatus("Getting GPS location...", "info");

    try {
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        });
      });

      this.verificationData.latitude = position.coords.latitude;
      this.verificationData.longitude = position.coords.longitude;
      this.verificationData.accuracy = position.coords.accuracy;

      // Display GPS info
      const gpsInfo = `
        <div class="alert alert-success">
          <strong>GPS Location Found!</strong><br>
          Latitude: ${this.verificationData.latitude.toFixed(6)}<br>
          Longitude: ${this.verificationData.longitude.toFixed(6)}<br>
          Accuracy: ±${Math.round(this.verificationData.accuracy)}m
        </div>
      `;
      document
        .getElementById("gps-info")
        ?.insertAdjacentHTML("afterbegin", gpsInfo);

      this.updateStatus("✓ GPS location acquired successfully", "success");
    } catch (error) {
      this.updateStatus(`✗ GPS Error: ${error.message}`, "danger");
    }
  }

  // ============ STEP 2: Camera & Face Capture ============

  async startCamera() {
    try {
      this.updateStatus("Initializing camera...", "info");

      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: "user",
        },
        audio: false,
      });

      this.video.srcObject = this.stream;
      this.video.play();

      document.getElementById("start-camera-btn")?.classList.add("d-none");
      document.getElementById("stop-camera-btn")?.classList.remove("d-none");
      document.getElementById("capture-controls")?.classList.remove("d-none");

      this.updateStatus(
        "✓ Camera ready! Position your face in the frame.",
        "success",
      );
    } catch (error) {
      this.updateStatus(`✗ Camera Error: ${error.message}`, "danger");
    }
  }

  stopCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }

    document.getElementById("stop-camera-btn")?.classList.add("d-none");
    document.getElementById("start-camera-btn")?.classList.remove("d-none");
    document.getElementById("capture-controls")?.classList.add("d-none");

    this.updateStatus("Camera stopped", "info");
  }

  captureFaceImage() {
    if (!this.stream) {
      this.updateStatus("Camera not started", "danger");
      return;
    }

    try {
      // Capture frame
      const context = this.canvas.getContext("2d");
      this.canvas.width = this.video.videoWidth;
      this.canvas.height = this.video.videoHeight;
      context.drawImage(this.video, 0, 0);

      // Convert to base64
      this.verificationData.faceImage = this.canvas.toDataURL("image/jpeg");

      // Display captured image
      const capturedImg = document.getElementById("captured-image");
      if (capturedImg) {
        capturedImg.src = this.verificationData.faceImage;
        capturedImg.classList.remove("d-none");
      }

      this.updateStatus("✓ Face image captured successfully", "success");
      document
        .getElementById("capture-face-btn")
        ?.classList.add("btn-disabled");
    } catch (error) {
      this.updateStatus(`✗ Capture Error: ${error.message}`, "danger");
    }
  }

  // ============ STEP 3: Liveness Detection ============

  async startLivenessDetection() {
    if (!this.stream) {
      this.updateStatus("Camera not started", "danger");
      return;
    }

    this.updateStatus(
      "Starting liveness detection... Please look at camera naturally",
      "info",
    );
    this.recordedFrames = [];
    this.recordingStartTime = Date.now();

    // Record frames for 5 seconds
    const recordDuration = 5000; // 5 seconds
    const captureInterval = 100; // Capture every 100ms

    this.recordingInterval = setInterval(() => {
      if (Date.now() - this.recordingStartTime > recordDuration) {
        clearInterval(this.recordingInterval);
        this.processLivenessFrames();
        return;
      }

      try {
        const context = this.canvas.getContext("2d");
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        context.drawImage(this.video, 0, 0);

        // Convert to base64 and store
        const frameData = this.canvas.toDataURL("image/jpeg");
        this.recordedFrames.push(frameData);

        // Update counter
        const elapsed = Math.floor(
          (Date.now() - this.recordingStartTime) / 1000,
        );
        document.getElementById("liveness-timer")?.textContent = `${elapsed}s`;
      } catch (error) {
        console.error("Error capturing frame:", error);
      }
    }, captureInterval);
  }

  async processLivenessFrames() {
    if (this.recordedFrames.length === 0) {
      this.updateStatus("✗ No frames recorded", "danger");
      return;
    }

    this.updateStatus("Processing liveness detection... Please wait", "info");

    try {
      this.verificationData.videoFrames = this.recordedFrames;

      // Send to backend for analysis if needed
      // For now, store frames for comprehensive attendance endpoint
      this.updateStatus(
        `✓ Recorded ${this.recordedFrames.length} frames for liveness analysis`,
        "success",
      );
    } catch (error) {
      this.updateStatus(
        `✗ Liveness Detection Error: ${error.message}`,
        "danger",
      );
    }
  }

  // ============ STEP 4: Challenge-Response ============

  async startChallengeVerification() {
    if (!this.stream) {
      this.updateStatus("Camera not started", "danger");
      return;
    }

    try {
      // Get random challenge
      const response = await fetch("/api/challenge/request", {
        method: "POST",
      });
      const data = await response.json();

      if (!data.success) {
        this.updateStatus("Failed to generate challenge", "danger");
        return;
      }

      const challenge = data.challenge;
      this.verificationData.challengeType = challenge.type;

      // Display challenge instruction
      const challengeMsg = `
        <div class="alert alert-info">
          <strong>Challenge: ${challenge.message}</strong><br>
          You have ${challenge.duration} seconds to complete this action.
        </div>
      `;
      this.statusArea.insertAdjacentHTML("afterbegin", challengeMsg);

      this.updateStatus(challenge.message, "info");

      // Record frames for challenge
      this.recordedFrames = [];
      this.recordingStartTime = Date.now();

      const recordDuration = challenge.duration * 1000;
      const captureInterval = 100;

      this.recordingInterval = setInterval(() => {
        if (Date.now() - this.recordingStartTime > recordDuration) {
          clearInterval(this.recordingInterval);
          this.processChallengeFrames();
          return;
        }

        try {
          const context = this.canvas.getContext("2d");
          this.canvas.width = this.video.videoWidth;
          this.canvas.height = this.video.videoHeight;
          context.drawImage(this.video, 0, 0);

          const frameData = this.canvas.toDataURL("image/jpeg");
          this.recordedFrames.push(frameData);
        } catch (error) {
          console.error("Error capturing challenge frame:", error);
        }
      }, captureInterval);
    } catch (error) {
      this.updateStatus(`✗ Challenge Error: ${error.message}`, "danger");
    }
  }

  async processChallengeFrames() {
    if (this.recordedFrames.length === 0) {
      this.updateStatus("✗ No frames recorded for challenge", "danger");
      return;
    }

    this.updateStatus("Validating challenge response...", "info");

    try {
      const response = await fetch("/api/challenge/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_id: this.verificationData.studentId,
          challenge_type: this.verificationData.challengeType,
          frames: this.recordedFrames,
        }),
      });

      const data = await response.json();

      if (data.success && data.challenge_passed) {
        this.verificationData.challengeFrames = this.recordedFrames;
        this.updateStatus(
          `✓ Challenge passed! (Confidence: ${(data.confidence * 100).toFixed(1)}%)`,
          "success",
        );
      } else {
        this.updateStatus(`✗ Challenge failed. Please try again.`, "danger");
        this.verificationData.challengeFrames = [];
      }
    } catch (error) {
      this.updateStatus(
        `✗ Challenge Validation Error: ${error.message}`,
        "danger",
      );
    }
  }

  // ============ STEP 5: Submit Comprehensive Attendance ============

  async submitAttendance() {
    // Validation
    if (!this.verificationData.studentId || !this.verificationData.classroom) {
      this.updateStatus("✗ Please select student and classroom", "danger");
      return;
    }

    if (!this.verificationData.latitude || !this.verificationData.longitude) {
      this.updateStatus("✗ Please get GPS location", "danger");
      return;
    }

    if (!this.verificationData.faceImage) {
      this.updateStatus("✗ Please capture face image", "danger");
      return;
    }

    if (this.verificationData.videoFrames.length === 0) {
      this.updateStatus("✗ Please complete liveness detection", "danger");
      return;
    }

    this.isProcessing = true;
    this.updateStatus(
      "Processing comprehensive attendance verification...",
      "info",
    );

    try {
      const payload = {
        student_id: this.verificationData.studentId,
        classroom: this.verificationData.classroom,
        latitude: this.verificationData.latitude,
        longitude: this.verificationData.longitude,
        accuracy: this.verificationData.accuracy,
        face_image: this.verificationData.faceImage,
        video_frames: this.verificationData.videoFrames,
        challenge_type: this.verificationData.challengeType,
        challenge_frames:
          this.verificationData.challengeFrames.length > 0
            ? this.verificationData.challengeFrames
            : null,
      };

      const response = await fetch("/api/attendance/mark-comprehensive", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const result = await response.json();

      if (result.success) {
        // Display success message with all details
        const successMsg = `
          <div class="alert alert-success" role="alert">
            <h4 class="alert-heading">✓ Attendance Marked Successfully!</h4>
            <hr>
            <p><strong>Student:</strong> ${result.student.name} (${result.student.id})</p>
            <p><strong>Classroom:</strong> ${result.classroom}</p>
            <p><strong>Time:</strong> ${new Date(result.timestamp).toLocaleString()}</p>
            <p><strong>GPS Distance:</strong> ${result.gps_distance_meters}m from classroom</p>
            <hr>
            <h5>Verification Steps Completed:</h5>
            <ul>
        `;

        result.verification_results.steps_passed.forEach((step) => {
          let details = ``;
          if (step.step === "GPS_LOCATION") {
            details = ` (${Math.round(step.distance_meters)}m)`;
          } else if (step.step === "FACE_RECOGNITION") {
            details = ` (Confidence: ${(step.confidence * 100).toFixed(1)}%)`;
          } else if (step.step === "LIVENESS_BLINK") {
            details = ` (${step.details.blink_detection.total_blinks} blinks detected)`;
          }

          const stepDisplay = step.step.replace(/_/g, " ");
          document
            .querySelector(".success-msg")
            ?.insertAdjacentHTML(
              "beforeend",
              `<li>${stepDisplay}${details}</li>`,
            );
        });

        this.updateStatus("✓ Attendance recorded successfully!", "success");

        // EMOTION DETECTION: Analyze emotion from face image after successful attendance
        this.updateStatus("Analyzing emotional state...", "info");
        await this.detectEmotionAfterAttendance(result.student.id);
      } else {
        // Display failure details
        let failureMsg = `<div class="alert alert-danger"><strong>✗ Attendance Verification Failed</strong><br>`;

        if (result.verification_results.steps_failed.length > 0) {
          failureMsg += `<h6>Failed Steps:</h6><ul>`;
          result.verification_results.steps_failed.forEach((step) => {
            failureMsg += `<li><strong>${step.step.replace(/_/g, " ")}:</strong> ${step.message}</li>`;
          });
          failureMsg += `</ul>`;
        }
        failureMsg += `</div>`;

        this.statusArea.insertAdjacentHTML("afterbegin", failureMsg);
        this.updateStatus(
          "Attendance verification failed. Please try again.",
          "danger",
        );
      }
    } catch (error) {
      this.updateStatus(`✗ Error: ${error.message}`, "danger");
    } finally {
      this.isProcessing = false;
    }
  }

  // ============ EMOTION DETECTION AFTER ATTENDANCE ============

  async detectEmotionAfterAttendance(studentId) {
    if (!this.verificationData.faceImage) {
      console.warn("[EMOTION] No face image available");
      this.updateStatus(
        "Could not analyze emotion - no face image available",
        "warning",
      );
      this.startNextVerificationTimer(10);
      return;
    }

    console.log("[EMOTION] Starting emotion detection...");

    try {
      const emotionPayload = {
        image: this.verificationData.faceImage,
        student_id: studentId,
      };

      // Set timeout for emotion detection (5 seconds max)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const emotionResponse = await fetch("/api/emotion/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(emotionPayload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!emotionResponse.ok) {
        throw new Error(`HTTP ${emotionResponse.status}: ${emotionResponse.statusText}`);
      }

      const emotionResult = await emotionResponse.json();
      console.log("[EMOTION] Response:", emotionResult);

      if (emotionResult.success && emotionResult.emotion && emotionResult.emotion !== "unknown") {
        const emotionMsg = `
          <div class="alert alert-info" role="alert">
            <h5 class="alert-heading">Emotional State Analysis</h5>
            <p><strong>${emotionResult.emoji || "😐"} Emotion:</strong> ${emotionResult.emotion}</p>
            <p><strong>Status:</strong> ${emotionResult.message}</p>
            <p><strong>Confidence:</strong> ${(emotionResult.confidence * 100).toFixed(1)}%</p>
          </div>
        `;
        this.statusArea.insertAdjacentHTML("afterbegin", emotionMsg);
        console.log(
          `[EMOTION] Detected: ${emotionResult.emotion} (${(emotionResult.confidence * 100).toFixed(1)}%)`,
        );
      } else {
        const failMsg = emotionResult.message || "Could not detect emotion";
        console.warn("[EMOTION] Detection returned unknown:", failMsg);
        this.updateStatus(
          `⚠️ Emotion detection inconclusive - retrying...",
          "warning",
        );
        // Retry emotion detection once
        setTimeout(() => this.retryEmotionDetection(studentId), 1000);
        return;
      }

      // After emotion detection, start 10-second timer for next verification
      this.startNextVerificationTimer(10);
    } catch (error) {
      if (error.name === "AbortError") {
        console.error("[EMOTION] Timeout - detection took too long");
        this.updateStatus("Emotion detection timed out. Proceeding...", "warning");
      } else {
        console.error("[EMOTION] Error:", error);
        this.updateStatus(
          `Emotion analysis error: ${error.message}`,
          "warning",
        );
      }
      this.startNextVerificationTimer(10);
    }
  }

  async retryEmotionDetection(studentId) {
    console.log("[EMOTION] Retrying emotion detection...");
    try {
      const emotionPayload = {
        image: this.verificationData.faceImage,
        student_id: studentId,
      };

      const emotionResponse = await fetch("/api/emotion/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(emotionPayload),
      });

      const emotionResult = await emotionResponse.json();
      console.log("[EMOTION] Retry Response:", emotionResult);

      if (emotionResult.success && emotionResult.emotion) {
        const emotionMsg = `
          <div class="alert alert-info" role="alert">
            <h5 class="alert-heading">Emotional State Analysis (Retry)</h5>
            <p><strong>${emotionResult.emoji || "😐"} Emotion:</strong> ${emotionResult.emotion}</p>
            <p><strong>Status:</strong> ${emotionResult.message}</p>
            <p><strong>Confidence:</strong> ${(emotionResult.confidence * 100).toFixed(1)}%</p>
          </div>
        `;
        this.statusArea.insertAdjacentHTML("afterbegin", emotionMsg);
        console.log(`[EMOTION] Retry Detected: ${emotionResult.emotion}`);
      } else {
        console.warn("[EMOTION] Retry also returned unknown");
      }

      this.startNextVerificationTimer(10);
    } catch (error) {
      console.error("[EMOTION] Retry failed:", error);
      this.startNextVerificationTimer(10);
    }
  }

  startNextVerificationTimer(seconds) {
    let timeRemaining = seconds;

    const timerMsg = `
      <div class="alert alert-warning alert-dismissible fade show" role="alert">
        <strong>Cooling-off Period Required</strong><br>
        <p>Next verification available in: <strong id="next-verification-timer">${timeRemaining}s</strong></p>
        <p>This ensures proper tracking and prevents duplicate entries.</p>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    `;
    this.statusArea.insertAdjacentHTML("afterbegin", timerMsg);

    const timerInterval = setInterval(() => {
      timeRemaining--;
      const timerElement = document.getElementById("next-verification-timer");
      if (timerElement) {
        timerElement.textContent = `${timeRemaining}s`;
      }

      if (timeRemaining <= 0) {
        clearInterval(timerInterval);
        // Re-enable buttons for next verification
        document.getElementById("submit-attendance-btn").disabled = false;
        this.updateStatus(
          "✓ Ready for next attendance verification!",
          "success",
        );
        // Auto-reset after timer completes
        this.resetForm();
      }
    }, 1000);

    // Disable submit button during cooldown
    document.getElementById("submit-attendance-btn").disabled = true;
  }

  // ============ UI Updates ============

  updateStatus(message, type = "info") {
    let alertClass = "alert-info";
    if (type === "success") alertClass = "alert-success";
    else if (type === "danger") alertClass = "alert-danger";
    else if (type === "warning") alertClass = "alert-warning";

    const alertHTML = `<div class="alert ${alertClass} alert-dismissible fade show" role="alert">
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>`;

    this.statusArea.insertAdjacentHTML("afterbegin", alertHTML);
    console.log(`[${type.toUpperCase()}] ${message}`);
  }

  updateProgressBar() {
    const progressBar = document.getElementById("progress-bar");
    if (progressBar) {
      const progress = (this.currentStep / this.steps.length) * 100;
      progressBar.style.width = progress + "%";
      progressBar.textContent = `Step ${this.currentStep + 1}/${this.steps.length}`;
    }
  }

  resetForm() {
    this.verificationData = {
      studentId: null,
      classroom: null,
      latitude: null,
      longitude: null,
      accuracy: null,
      faceImage: null,
      videoFrames: [],
      challengeType: null,
      challengeFrames: [],
    };
    this.currentStep = 0;
    this.recordedFrames = [];

    document.getElementById("student-select").value = "";
    document.getElementById("classroom-select").value = "";
    document.getElementById("captured-image")?.classList.add("d-none");
    document.getElementById("gps-info").innerHTML = "";

    this.updateStatus(
      "Form reset. Ready for new attendance verification.",
      "info",
    );
    this.updateProgressBar();
  }
}

// Initialize when page loads
document.addEventListener("DOMContentLoaded", () => {
  window.attendanceSystem = new AttendanceVerificationSystem();
});
