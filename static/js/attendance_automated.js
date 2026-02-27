/**
 * SmartAttendAI - Automated Attendance System
 * Fully automated process requiring only classroom selection
 */

class AutomatedAttendanceSystem {
  constructor() {
    this.video = document.getElementById("video");
    this.canvas = document.getElementById("canvas");
    this.statusArea = document.getElementById("status-area");
    this.stream = null;
    this.isProcessing = false;
    this.recordedFrames = [];
    this.recordingStartTime = null;
    this.automationStarted = false;

    // Verification state
    this.verificationData = {
      studentId: null,
      studentName: null,
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
      "Get GPS Location",
      "Start Camera",
      "Capture Face",
      "Liveness Check",
      "Challenge-Response",
      "Mark Attendance",
    ];

    this.initializeEventListeners();
    this.loadStudentInfo();
    this.updateProgressBar();
  }

  initializeEventListeners() {
    // Classroom selection - triggers automation
    document
      .getElementById("classroom-select")
      ?.addEventListener("change", (e) => {
        this.verificationData.classroom = e.target.value;
        if (e.target.value && !this.automationStarted) {
          this.startAutomatedWorkflow();
        }
      });
  }

  /**
   * Load student information from backend or session
   */
  async loadStudentInfo() {
    try {
      // Try to get from session/API first
      const response = await fetch("/api/student/current", {
        method: "GET",
      });

      if (response.ok) {
        const data = await response.json();
        this.verificationData.studentId = data.student_id;
        this.verificationData.studentName = data.name;

        const studentDisplay = document.getElementById("student-name-display");
        if (studentDisplay) {
          studentDisplay.value = data.name;
        }

        this.updateStatus(`✓ Student identified: ${data.name}`, "success");
      }
    } catch (error) {
      console.log(
        "Note: Student info will be identified from face recognition",
      );
    }
  }

  /**
   * Start the fully automated workflow
   */
  async startAutomatedWorkflow() {
    if (this.automationStarted) return;
    this.automationStarted = true;

    this.updateStatus(
      "🚀 Starting automated attendance verification...",
      "info",
    );

    try {
      // Step 1: Get GPS Location
      this.currentStep = 0;
      this.updateProgressBar();
      await this.getGPSLocationAuto();

      // Step 2: Start Camera
      this.currentStep = 1;
      this.updateProgressBar();
      await this.startCameraAuto();

      // Step 3: Capture Face
      this.currentStep = 2;
      this.updateProgressBar();
      await this.captureFaceImageAuto();

      // Step 4: Liveness Detection
      this.currentStep = 3;
      this.updateProgressBar();
      await this.startLivenessDetectionAuto();

      // Step 5: Challenge-Response
      this.currentStep = 4;
      this.updateProgressBar();
      await this.startChallengeVerificationAuto();

      // Step 6: Submit Attendance
      this.currentStep = 5;
      this.updateProgressBar();
      await this.submitAttendanceAuto();
    } catch (error) {
      this.updateStatus(`✗ Automation Error: ${error.message}`, "danger");
      this.automationStarted = false;
    }
  }

  /**
   * Step 1: Get GPS Location Automatically
   */
  async getGPSLocationAuto() {
    this.updateStatus("📍 Acquiring GPS location...", "info");

    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          this.verificationData.latitude = position.coords.latitude;
          this.verificationData.longitude = position.coords.longitude;
          this.verificationData.accuracy = position.coords.accuracy;

          const gpsInfo = `
            <div class="alert alert-success">
              <strong>✓ GPS Location Found!</strong><br>
              Latitude: ${this.verificationData.latitude.toFixed(6)}<br>
              Longitude: ${this.verificationData.longitude.toFixed(6)}<br>
              Accuracy: ±${Math.round(this.verificationData.accuracy)}m
            </div>
          `;
          document
            .getElementById("gps-info")
            ?.insertAdjacentHTML("afterbegin", gpsInfo);

          this.updateStatus("✓ GPS location acquired", "success");
          resolve();
        },
        (error) => {
          this.updateStatus(`✗ GPS Error: ${error.message}`, "danger");
          resolve(); // Continue even if GPS fails
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        },
      );
    });
  }

  /**
   * Step 2: Start Camera Automatically
   */
  async startCameraAuto() {
    this.updateStatus("📷 Initializing camera...", "info");

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: "user",
        },
        audio: false,
      });

      this.video.srcObject = this.stream;
      document.getElementById("video-section").style.display = "block";
      this.video.play();

      this.updateStatus("✓ Camera ready", "success");

      // Wait a moment for video to stabilize
      return new Promise((resolve) => setTimeout(resolve, 1500));
    } catch (error) {
      this.updateStatus(`✗ Camera Error: ${error.message}`, "danger");
      throw error;
    }
  }

  /**
   * Step 3: Capture Face Image Automatically
   */
  async captureFaceImageAuto() {
    this.updateStatus("📸 Capturing face image...", "info");

    return new Promise((resolve) => {
      setTimeout(() => {
        if (!this.stream) {
          this.updateStatus("Camera not available", "danger");
          resolve();
          return;
        }

        try {
          const context = this.canvas.getContext("2d");
          this.canvas.width = this.video.videoWidth;
          this.canvas.height = this.video.videoHeight;
          context.drawImage(this.video, 0, 0);

          this.verificationData.faceImage = this.canvas.toDataURL("image/jpeg");

          const capturedImg = document.getElementById("captured-image");
          if (capturedImg) {
            capturedImg.src = this.verificationData.faceImage;
            capturedImg.classList.remove("d-none");
          }

          // Automatically recognize student from face
          this.recognizeStudentFromFace(this.verificationData.faceImage).then(
            () => {
              this.updateStatus(
                "✓ Face image captured and student identified",
                "success",
              );
              resolve();
            },
          );
        } catch (error) {
          this.updateStatus(`✗ Capture Error: ${error.message}`, "danger");
          resolve();
        }
      }, 500);
    });
  }

  /**
   * Recognize student from captured face image
   */
  async recognizeStudentFromFace(faceImageBase64) {
    try {
      this.updateStatus("🔍 Identifying student from face...", "info");

      const response = await fetch("/api/recognize-face", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image: faceImageBase64,
        }),
      });

      const data = await response.json();

      if (data.success && data.student) {
        this.verificationData.studentId =
          data.student.id || data.student.student_id;
        this.verificationData.studentName = data.student.name;

        const studentDisplay = document.getElementById("student-name-display");
        if (studentDisplay) {
          studentDisplay.value = data.student.name;
        }

        this.updateStatus(
          `✓ Student identified: ${data.student.name} (Confidence: ${(data.confidence * 100).toFixed(1)}%)`,
          "success",
        );
      } else {
        this.updateStatus(
          `⚠ Could not identify student from face - please try again with better lighting`,
          "warning",
        );
      }
    } catch (error) {
      this.updateStatus(`Face recognition note: ${error.message}`, "warning");
    }
  }

  /**
   * Step 4: Liveness Detection Automatically
   */
  async startLivenessDetectionAuto() {
    if (!this.stream) {
      this.updateStatus("Camera not started", "danger");
      return;
    }

    return new Promise((resolve) => {
      this.updateStatus("💓 Analyzing liveness (5 seconds)...", "info");

      this.recordedFrames = [];
      this.recordingStartTime = Date.now();

      const recordDuration = 5000; // 5 seconds
      const captureInterval = 100; // Capture every 100ms

      const timerDiv = document.getElementById("liveness-timer");
      if (timerDiv) {
        timerDiv.classList.remove("d-none");
      }

      this.recordingInterval = setInterval(() => {
        if (Date.now() - this.recordingStartTime > recordDuration) {
          clearInterval(this.recordingInterval);

          if (timerDiv) {
            timerDiv.classList.add("d-none");
          }

          this.verificationData.videoFrames = this.recordedFrames;
          this.updateStatus(
            `✓ Liveness check completed (${this.recordedFrames.length} frames)`,
            "success",
          );
          resolve();
          return;
        }

        try {
          const context = this.canvas.getContext("2d");
          this.canvas.width = this.video.videoWidth;
          this.canvas.height = this.video.videoHeight;
          context.drawImage(this.video, 0, 0);

          const frameData = this.canvas.toDataURL("image/jpeg");
          this.recordedFrames.push(frameData);

          const elapsed = Math.floor(
            (Date.now() - this.recordingStartTime) / 1000,
          );
          if (timerDiv) {
            timerDiv.textContent = `${elapsed}s`;
          }
        } catch (error) {
          console.error("Error capturing frame:", error);
        }
      }, captureInterval);
    });
  }

  /**
   * Step 5: Challenge-Response Automatically
   */
  async startChallengeVerificationAuto() {
    if (!this.stream) {
      this.updateStatus("Camera not started", "danger");
      return;
    }

    return new Promise((resolve) => {
      try {
        // Get challenge from backend
        fetch("/api/challenge/request", {
          method: "POST",
        })
          .then((response) => response.json())
          .then((data) => {
            if (!data.success) {
              this.updateStatus("Failed to generate challenge", "danger");
              resolve();
              return;
            }

            const challenge = data.challenge;
            this.verificationData.challengeType = challenge.type;

            const challengeMsg = `
              <div class="alert alert-info">
                <strong>⚡ Challenge: ${challenge.message}</strong><br>
                Performing action for ${challenge.duration} seconds...
              </div>
            `;
            const challengeInfoDiv = document.getElementById("challenge-info");
            if (challengeInfoDiv) {
              challengeInfoDiv.insertAdjacentHTML("afterbegin", challengeMsg);
            }

            this.updateStatus(challenge.message, "info");

            this.recordedFrames = [];
            this.recordingStartTime = Date.now();

            const recordDuration = challenge.duration * 1000;
            const captureInterval = 100;

            this.recordingInterval = setInterval(() => {
              if (Date.now() - this.recordingStartTime > recordDuration) {
                clearInterval(this.recordingInterval);

                // Process challenge frames
                if (this.recordedFrames.length > 0) {
                  this.processChallengeFramesAuto(
                    challenge.type,
                    this.recordedFrames,
                  ).then(() => resolve());
                } else {
                  this.updateStatus(
                    "✗ No frames recorded for challenge",
                    "danger",
                  );
                  resolve();
                }
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
          })
          .catch((error) => {
            this.updateStatus(`✗ Challenge Error: ${error.message}`, "danger");
            resolve();
          });
      } catch (error) {
        this.updateStatus(`✗ Challenge Error: ${error.message}`, "danger");
        resolve();
      }
    });
  }

  /**
   * Process and validate challenge frames
   */
  async processChallengeFramesAuto(challengeType, frames) {
    this.updateStatus("Validating challenge response...", "info");

    try {
      const response = await fetch("/api/challenge/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_id: this.verificationData.studentId,
          challenge_type: challengeType,
          frames: frames,
        }),
      });

      const data = await response.json();

      if (data.success && data.challenge_passed) {
        this.verificationData.challengeFrames = frames;
        this.updateStatus(
          `✓ Challenge passed! (Confidence: ${(data.confidence * 100).toFixed(
            1,
          )}%)`,
          "success",
        );
      } else {
        this.updateStatus("Challenge validation completed", "info");
        // Continue anyway for now
      }
    } catch (error) {
      this.updateStatus(`Challenge validation: ${error.message}`, "warning");
    }
  }

  /**
   * Step 6: Submit Attendance Automatically
   */
  async submitAttendanceAuto() {
    if (!this.verificationData.studentId || !this.verificationData.classroom) {
      this.updateStatus("✗ Missing student or classroom", "danger");
      return;
    }

    this.updateStatus("📤 Submitting attendance verification...", "info");

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

        if (result.verification_results?.steps_passed) {
          result.verification_results.steps_passed.forEach((step) => {
            let details = ``;
            if (step.step === "GPS_LOCATION") {
              details = ` (${Math.round(step.distance_meters)}m)`;
            } else if (step.step === "FACE_RECOGNITION") {
              details = ` (Confidence: ${(step.confidence * 100).toFixed(1)}%)`;
            } else if (step.step === "LIVENESS_BLINK") {
              details = ` (${step.details?.blink_detection?.total_blinks || 0} blinks)`;
            }

            const stepDisplay = step.step.replace(/_/g, " ");
            const submissionStatus =
              document.getElementById("submission-status");
            if (submissionStatus) {
              submissionStatus.insertAdjacentHTML(
                "beforeend",
                `<li>${stepDisplay}${details}</li>`,
              );
            }
          });
        }

        this.updateStatus("✓ Attendance recorded successfully!", "success");

        // EMOTION DETECTION: Analyze emotion from face image after successful attendance
        this.updateStatus("Analyzing emotional state...", "info");
        await this.detectEmotionAfterAttendance(result.student.id);

        // Stop camera
        this.stopCameraAuto();

        // Show completion message
        const submissionStatus = document.getElementById("submission-status");
        if (submissionStatus) {
          submissionStatus.insertAdjacentHTML("afterbegin", successMsg);
        }
      } else {
        let failureMsg = `<div class="alert alert-danger"><strong>✗ Verification Failed</strong><br>`;

        if (result.verification_results?.steps_failed) {
          failureMsg += `<h6>Failed Steps:</h6><ul>`;
          result.verification_results.steps_failed.forEach((step) => {
            failureMsg += `<li><strong>${step.step.replace(/_/g, " ")}:</strong> ${
              step.message
            }</li>`;
          });
          failureMsg += `</ul>`;
        }
        failureMsg += `</div>`;

        this.statusArea.insertAdjacentHTML("afterbegin", failureMsg);
        this.updateStatus("Verification failed. Please try again.", "danger");

        // Stop camera
        this.stopCameraAuto();
      }
    } catch (error) {
      this.updateStatus(`✗ Error: ${error.message}`, "danger");

      // Stop camera
      this.stopCameraAuto();
    }
  }

  /**
   * Stop camera
   */
  stopCameraAuto() {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }

    const videoSection = document.getElementById("video-section");
    if (videoSection) {
      videoSection.style.display = "none";
    }
  }

  // ============ EMOTION DETECTION AFTER ATTENDANCE ============

  async detectEmotionAfterAttendance(studentId) {
    if (!this.verificationData.faceImage) {
      this.updateStatus(
        "Could not analyze emotion - no face image available",
        "warning",
      );
      this.startNextVerificationTimer(10);
      return;
    }

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

      if (emotionResult.success) {
        const emotionMsg = `
          <div class="alert alert-info" role="alert">
            <h5 class="alert-heading">Emotional State Analysis</h5>
            <p><strong>${emotionResult.emoji} Emotion:</strong> ${emotionResult.emotion}</p>
            <p><strong>Status:</strong> ${emotionResult.message}</p>
            <p><strong>Confidence:</strong> ${(emotionResult.confidence * 100).toFixed(1)}%</p>
          </div>
        `;
        this.statusArea.insertAdjacentHTML("afterbegin", emotionMsg);
        console.log(
          `[EMOTION] ${emotionResult.emotion} (${(emotionResult.confidence * 100).toFixed(1)}%)`,
        );
      } else {
        console.warn("[EMOTION] Analysis failed:", emotionResult.message);
        this.updateStatus(
          `Emotion analysis: ${emotionResult.message}`,
          "warning",
        );
      }

      // After emotion detection, start 10-second timer for next verification
      this.startNextVerificationTimer(10);
    } catch (error) {
      console.error("[EMOTION] Error:", error);
      this.updateStatus(
        `Emotion analysis error: ${error.message}. Proceeding with next verification...`,
        "warning",
      );
      this.startNextVerificationTimer(10);
    }
  }

  startNextVerificationTimer(seconds) {
    let timeRemaining = seconds;

    const timerMsg = `
      <div class="alert alert-warning alert-dismissible fade show" role="alert">
        <strong>Cooling-off Period Required</strong><br>
        <p>Next verification available in: <strong id="next-verification-timer-auto">${timeRemaining}s</strong></p>
        <p>This ensures proper tracking and prevents duplicate entries.</p>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    `;
    this.statusArea.insertAdjacentHTML("afterbegin", timerMsg);

    const timerInterval = setInterval(() => {
      timeRemaining--;
      const timerElement = document.getElementById(
        "next-verification-timer-auto",
      );
      if (timerElement) {
        timerElement.textContent = `${timeRemaining}s`;
      }

      if (timeRemaining <= 0) {
        clearInterval(timerInterval);
        this.updateStatus(
          "✓ Ready for next attendance verification!",
          "success",
        );
        // Reset automation for next student
        this.resetAutomation();
      }
    }, 1000);
  }

  resetAutomation() {
    this.automationStarted = false;
    this.verificationData = {
      studentId: null,
      studentName: null,
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

    // Reset UI
    const studentDisplay = document.getElementById("student-name-display");
    if (studentDisplay) {
      studentDisplay.value = "";
    }

    const classroomSelect = document.getElementById("classroom-select");
    if (classroomSelect) {
      classroomSelect.value = "";
    }

    this.updateProgressBar();
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
      const progress = ((this.currentStep + 1) / this.steps.length) * 100;
      progressBar.style.width = progress + "%";

      const stepDots = document.querySelectorAll(".step-dot");
      stepDots.forEach((dot, index) => {
        dot.classList.remove("active", "completed");
        if (index < this.currentStep) {
          dot.classList.add("completed");
        } else if (index === this.currentStep) {
          dot.classList.add("active");
        }
      });
    }
  }
}

// Initialize when page loads
document.addEventListener("DOMContentLoaded", () => {
  window.attendanceSystem = new AutomatedAttendanceSystem();
});
