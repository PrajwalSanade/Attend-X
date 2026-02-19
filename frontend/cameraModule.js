// ============================================
// CAMERA MODULE - PRODUCTION READY
// ============================================
// Handles camera access, photo capture, and cleanup
// Works on localhost and HTTPS
// Background-independent face capture
// ============================================

let stream = null;
let imageBase64 = null;
let isProcessing = false;

/**
 * Open camera and display video stream
 * @param {HTMLVideoElement} videoEl - Video element to display stream
 * @param {HTMLButtonElement} captureBtn - Capture button to show
 * @returns {Promise<void>}
 */
export async function openCamera(videoEl, captureBtn) {
  if (isProcessing) {
    console.warn('⚠️ Camera operation already in progress');
    return;
  }

  try {
    isProcessing = true;
    console.log('📷 Opening camera...');

    // Check browser support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('Camera API not supported in this browser. Please use Chrome, Firefox, or Edge.');
    }

    // Stop any existing stream first
    if (stream) {
      console.log('🛑 Stopping existing camera stream');
      stopCamera();
    }

    // Request camera access with optimal settings
    const constraints = {
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'user' // Front camera on mobile
      },
      audio: false
    };

    console.log('🎥 Requesting camera permission...');
    stream = await navigator.mediaDevices.getUserMedia(constraints);
    
    console.log('✅ Camera permission granted');
    console.log('📹 Stream tracks:', stream.getTracks().length);

    // Attach stream to video element
    videoEl.srcObject = stream;
    videoEl.style.display = 'block';
    
    // Wait for video to be ready
    await new Promise((resolve, reject) => {
      videoEl.onloadedmetadata = () => {
        console.log('📺 Video metadata loaded');
        resolve();
      };
      videoEl.onerror = (error) => {
        console.error('❌ Video element error:', error);
        reject(new Error('Failed to load video stream'));
      };
      
      // Timeout after 10 seconds
      setTimeout(() => reject(new Error('Camera timeout')), 10000);
    });

    // Play video
    await videoEl.play();
    console.log('▶️ Video playing');

    // Show capture button
    if (captureBtn) {
      captureBtn.style.display = 'inline-block';
      console.log('✅ Capture button shown');
    }

    console.log('✅ Camera opened successfully');
    
  } catch (error) {
    console.error('❌ Camera error:', error);
    
    // Clean up on error
    stopCamera();
    
    // Provide user-friendly error messages
    let errorMessage = 'Failed to open camera. ';
    
    if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
      errorMessage += 'Camera permission denied. Please allow camera access in your browser settings.';
    } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
      errorMessage += 'No camera found. Please connect a camera and try again.';
    } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
      errorMessage += 'Camera is already in use by another application.';
    } else if (error.name === 'OverconstrainedError') {
      errorMessage += 'Camera does not support the required settings.';
    } else if (error.name === 'SecurityError') {
      errorMessage += 'Camera access blocked. Please use HTTPS or localhost.';
    } else {
      errorMessage += error.message || 'Unknown error occurred.';
    }
    
    throw new Error(errorMessage);
  } finally {
    isProcessing = false;
  }
}

/**
 * Capture photo from video stream
 * @param {HTMLVideoElement} videoEl - Video element with stream
 * @param {HTMLCanvasElement} canvasEl - Canvas for capture
 * @returns {string} Base64 encoded image
 */
export function capturePhoto(videoEl, canvasEl) {
  try {
    console.log('📸 Capturing photo...');

    if (!stream) {
      throw new Error('Camera not started. Please open camera first.');
    }

    if (!videoEl.videoWidth || !videoEl.videoHeight) {
      throw new Error('Video not ready. Please wait for camera to initialize.');
    }

    // Set canvas size to match video
    canvasEl.width = videoEl.videoWidth;
    canvasEl.height = videoEl.videoHeight;

    console.log(`📐 Canvas size: ${canvasEl.width}x${canvasEl.height}`);

    // Draw current video frame to canvas
    const ctx = canvasEl.getContext('2d');
    ctx.drawImage(videoEl, 0, 0, canvasEl.width, canvasEl.height);

    // Convert to base64 JPEG (smaller file size than PNG)
    imageBase64 = canvasEl.toDataURL('image/jpeg', 0.9);

    console.log('✅ Photo captured');
    console.log(`📦 Image size: ${Math.round(imageBase64.length / 1024)}KB`);

    // Stop camera after capture
    stopCamera();

    // Hide video element
    videoEl.style.display = 'none';

    return imageBase64;
    
  } catch (error) {
    console.error('❌ Capture error:', error);
    throw new Error('Failed to capture photo: ' + error.message);
  }
}

/**
 * Upload photo from file input
 * @param {File} file - Image file from input
 * @returns {Promise<string>} Base64 encoded image
 */
export function uploadPhoto(file) {
  return new Promise((resolve, reject) => {
    try {
      console.log('📤 Uploading photo from file...');

      // Validate file
      if (!file) {
        reject(new Error('No file selected'));
        return;
      }

      if (!file.type.startsWith('image/')) {
        reject(new Error('Invalid file type. Please select an image file.'));
        return;
      }

      // Check file size (max 5MB)
      const maxSize = 5 * 1024 * 1024; // 5MB
      if (file.size > maxSize) {
        reject(new Error('File too large. Maximum size is 5MB.'));
        return;
      }

      console.log(`📁 File: ${file.name} (${Math.round(file.size / 1024)}KB)`);

      // Read file as base64
      const reader = new FileReader();
      
      reader.onload = () => {
        imageBase64 = reader.result;
        console.log('✅ Photo uploaded successfully');
        console.log(`📦 Image size: ${Math.round(imageBase64.length / 1024)}KB`);
        resolve(imageBase64);
      };
      
      reader.onerror = () => {
        console.error('❌ File read error:', reader.error);
        reject(new Error('Failed to read file: ' + reader.error));
      };
      
      reader.readAsDataURL(file);
      
    } catch (error) {
      console.error('❌ Upload error:', error);
      reject(new Error('Failed to upload photo: ' + error.message));
    }
  });
}

/**
 * Stop camera and release resources
 */
export function stopCamera() {
  try {
    if (stream) {
      console.log('🛑 Stopping camera...');
      
      // Stop all tracks
      stream.getTracks().forEach(track => {
        track.stop();
        console.log(`⏹️ Stopped track: ${track.kind}`);
      });
      
      stream = null;
      console.log('✅ Camera stopped');
    }
  } catch (error) {
    console.error('❌ Error stopping camera:', error);
  }
}

/**
 * Get captured/uploaded image
 * @returns {string|null} Base64 encoded image
 */
export function getImage() {
  return imageBase64;
}

/**
 * Clear stored image
 */
export function clearImage() {
  imageBase64 = null;
  console.log('🗑️ Image cleared');
}

/**
 * Check if camera is currently active
 * @returns {boolean}
 */
export function isCameraActive() {
  return stream !== null && stream.active;
}

// ============================================
// CLEANUP ON PAGE UNLOAD
// ============================================
window.addEventListener('beforeunload', () => {
  stopCamera();
});

console.log('✅ Camera module loaded');
