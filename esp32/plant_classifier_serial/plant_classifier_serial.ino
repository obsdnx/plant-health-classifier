/*
  Plant Health Classifier — ESP32-CAM via USB Serial (no WiFi needed)
  Board: AI Thinker ESP32-CAM

  Protocol:
    1. Laptop sends "CAPTURE\n" over serial
    2. ESP32 takes a photo
    3. ESP32 sends "IMG:<length>\n" then the raw JPEG bytes
    4. Laptop reads the bytes and sends to the classifier server

  Or just press GPIO 0 (flash button) to trigger automatically.

  Board settings:
    Board:           AI Thinker ESP32-CAM
    Partition Scheme: Huge APP (3MB No OTA)
    Upload Speed:    115200
*/

#include "esp_camera.h"

#define BUTTON_PIN 0

#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

bool cameraReady = false;

void setup() {
  Serial.begin(921600);   // high baud rate so images transfer fast
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  initCamera();
  Serial.println("READY");
}

void loop() {
  // Trigger on button press
  if (digitalRead(BUTTON_PIN) == LOW) {
    delay(50);
    if (digitalRead(BUTTON_PIN) == LOW) {
      sendPhoto();
      while (digitalRead(BUTTON_PIN) == LOW) delay(10);
    }
  }

  // Trigger on "CAPTURE" command from laptop
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "CAPTURE") {
      sendPhoto();
    }
  }
}

void initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM; config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM; config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM; config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM; config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size   = FRAMESIZE_SVGA;
  config.jpeg_quality = 12;
  config.fb_count     = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("ERROR:Camera init failed");
    return;
  }
  cameraReady = true;
}

void sendPhoto() {
  if (!cameraReady) { Serial.println("ERROR:Camera not ready"); return; }

  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) { Serial.println("ERROR:Capture failed"); return; }

  // Send header then raw bytes
  Serial.printf("IMG:%d\n", fb->len);
  Serial.write(fb->buf, fb->len);
  Serial.flush();

  esp_camera_fb_return(fb);
}
