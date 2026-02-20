import cv2
import mediapipe as mp
import time
import pyautogui
import numpy as np
import math
import random
import tkinter as tk
from tkinter import filedialog
from PIL import ImageFont, ImageDraw, Image
import pygame.mixer # 에러가 없는 오디오 믹서 전용 모듈

# --- 오디오 믹서 초기화 ---
pygame.mixer.init()

# --- 바탕화면 효과용 투명 창 설정 ---
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-transparentcolor", "white")
sw, sh = pyautogui.size()
root.geometry(f"{sw}x{sh}+0+0")
canvas = tk.Canvas(root, width=sw, height=sh, bg="white", highlightthickness=0)
canvas.pack()

active_particles = []

def create_shell_hole(x, y):
    canvas.create_oval(x-100, y-100, x+100, y+100, fill="#111111", outline="#333333", width=5, tags="crack")
    for _ in range(12):
        angle = random.uniform(0, 2*math.pi)
        length = random.randint(100, 250)
        tx, ty = x + math.cos(angle)*length, y + random.randint(-50, 50)
        canvas.create_line(x, y, tx, ty, fill="black", width=3, tags="crack")
    for _ in range(30):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(8, 20)
        p_color = random.choice(["#FF4500", "#FFD700", "#FFFFFF", "#333333"])
        p_id = canvas.create_oval(x-6, y-6, x+6, y+6, fill=p_color, outline="")
        active_particles.append({"id": p_id, "vx": math.cos(angle)*speed, "vy": math.sin(angle)*speed, "life": 25})

def update_visual_effects():
    for p in active_particles[:]:
        canvas.move(p["id"], p["vx"], p["vy"])
        p["life"] -= 1
        if p["life"] <= 0:
            canvas.delete(p["id"])
            active_particles.remove(p)

# ==========================================
# 사용자님 원본 초기 설정
# ==========================================
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

typing_mode = False
funny_mode = False  
selected_concept = None 
is_hangul_mode = False 
prev_x, prev_y = 0, 0
smooth_factor = 0.2
last_action_time = 0

# ==========================================
# [추가] DJ 모드 상태 관리
# ==========================================
dj_mode = False
dj_setup = True # True면 파일 업로드 화면, False면 디제잉 화면
dj_state = {
    "left_path": None, "right_path": None,
    "left_ch": None, "right_ch": None,
    # 슬라이더 값 (0.0 ~ 1.0)
    "vol_L": 0.5, "echo_L": 0.0, "time_L": 0.0,
    "vol_R": 0.5, "echo_R": 0.0, "time_R": 0.0,
    "crossfader": 0.5, # 0.0(Left Only) ~ 1.0(Right Only)
    "spin_L": 0, "spin_R": 0 # 원판 회전 각도
}

try:
    font = ImageFont.truetype("malgun.ttf", 20)
    large_font = ImageFont.truetype("malgun.ttf", 30)
except:
    font = ImageFont.load_default()
    large_font = ImageFont.load_default()

funny_concepts = ["바탕화면 파괴", "레이저"]

en_keys = [
    ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
    ["a", "s", "d", "f", "g", "h", "j", "k", "l", "lang"],
    ["z", "x", "c", "v", "b", "n", "m", "sync", "space", "ent"] 
]
ko_keys = [
    ["ㅂ", "ㅈ", "ㄷ", "ㄱ", "ㅅ", "ㅛ", "ㅕ", "ㅑ", "ㅐ", "ㅔ"],
    ["ㅁ", "ㄴ", "ㅇ", "ㄹ", "ㅎ", "ㅗ", "ㅓ", "ㅏ", "ㅣ", "한/영"],
    ["ㅋ", "ㅌ", "ㅊ", "ㅍ", "ㅠ", "ㅜ", "ㅡ", "싱크", "공백", "엔터"]
]

HAND_CONNECTIONS = [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(0,9),(9,10),(10,11),(11,12),(0,13),(13,14),(14,15),(15,16),(0,17),(17,18),(18,19),(19,20),(5,9),(9,13),(13,17)]

def draw_text_kor(img, text, position, font, color):
    img_pil = Image.fromarray(img)
    draw = ImageDraw.Draw(img_pil)
    draw.text(position, text, font=font, fill=color)
    return np.array(img_pil)

def draw_keyboard(img, current_targets):
    current_layout = ko_keys if is_hangul_mode else en_keys
    for r, row in enumerate(current_layout):
        for c, key in enumerate(row):
            kx, ky = 40 + c*60, 180 + r*60
            color = (255, 100, 0)
            for tx, ty in current_targets:
                if kx < tx < kx+55 and ky < ty < ky+55: color = (0, 255, 255)
            cv2.rectangle(img, (kx, ky), (kx+55, ky+55), color, 2)
            img = draw_text_kor(img, key.upper() if not is_hangul_mode else key, (kx+5, ky+15), font, (255, 255, 255))
    return img

def draw_funny_menu(img, finger_pos):
    h, w, _ = img.shape
    overlay = img.copy()
    cv2.rectangle(overlay, (50, 50), (350, 200), (0, 0, 0), -1) 
    cv2.addWeighted(overlay, 0.5, img, 0.5, 0, img)
    img = draw_text_kor(img, "★ FUNNY SELECT ★", (70, 70), font, (0, 255, 255))
    selected_idx = -1
    for i, concept in enumerate(funny_concepts):
        bx, by = 70, 110 + i*60
        color = (255, 255, 255)
        for fx, fy in finger_pos:
            if bx < fx < bx+250 and by < fy < by+50:
                color = (0, 255, 0)
                selected_idx = i
        cv2.rectangle(img, (bx, by), (bx+250, by+50), color, 2)
        img = draw_text_kor(img, concept, (bx+60, by+10), font, color)
    return img, selected_idx

# ==========================================
# [추가] DJ 모드 UI 그리기 및 인터랙션 처리 함수
# ==========================================
def process_dj_mode(img, finger_pos):
    global dj_setup, last_action_time
    h, w, _ = img.shape
    
    # [1단계] 파일 업로드 화면
    if dj_setup:
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.8, img, 0.2, 0, img)
        img = draw_text_kor(img, "DJ MODE : 음악 파일 2개를 업로드하세요", (w//2 - 200, 50), large_font, (0, 255, 255))
        
        # 버튼 영역
        btn_L = (w//4 - 100, h//2 - 50, w//4 + 100, h//2 + 50)
        btn_R = (3*w//4 - 100, h//2 - 50, 3*w//4 + 100, h//2 + 50)
        
        color_L = (0, 255, 0) if dj_state["left_path"] else (200, 200, 200)
        color_R = (0, 255, 0) if dj_state["right_path"] else (200, 200, 200)
        
        # 손가락 터치 인식 (클릭 없이 닿기만 하면 열림)
        for fx, fy in finger_pos:
            if btn_L[0] < fx < btn_L[2] and btn_L[1] < fy < btn_L[3] and time.time() - last_action_time > 2.0:
                filepath = filedialog.askopenfilename(title="왼쪽 음악 선택", filetypes=[("Audio", "*.mp3 *.wav *.ogg")])
                if filepath: 
                    dj_state["left_path"] = filepath
                    dj_state["left_ch"] = pygame.mixer.Sound(filepath)
                last_action_time = time.time()
                
            if btn_R[0] < fx < btn_R[2] and btn_R[1] < fy < btn_R[3] and time.time() - last_action_time > 2.0:
                filepath = filedialog.askopenfilename(title="오른쪽 음악 선택", filetypes=[("Audio", "*.mp3 *.wav *.ogg")])
                if filepath: 
                    dj_state["right_path"] = filepath
                    dj_state["right_ch"] = pygame.mixer.Sound(filepath)
                last_action_time = time.time()

        cv2.rectangle(img, (btn_L[0], btn_L[1]), (btn_L[2], btn_L[3]), color_L, 3)
        img = draw_text_kor(img, "LEFT MUSIC LOAD" if not dj_state["left_path"] else "LEFT READY", (btn_L[0]+20, btn_L[1]+35), font, color_L)
        
        cv2.rectangle(img, (btn_R[0], btn_R[1]), (btn_R[2], btn_R[3]), color_R, 3)
        img = draw_text_kor(img, "RIGHT MUSIC LOAD" if not dj_state["right_path"] else "RIGHT READY", (btn_R[0]+15, btn_R[1]+35), font, color_R)

        # 둘 다 로드되었으면 자동 다음 단계 + 음악 재생
        if dj_state["left_path"] and dj_state["right_path"]:
            if time.time() - last_action_time > 1.5:
                dj_setup = False
                dj_state["left_ch"].play(loops=-1)
                dj_state["right_ch"].play(loops=-1)
                last_action_time = time.time()

    # [2단계] DJ 믹서 화면
    else:
        # 4등분 선 긋기
        cv2.line(img, (w//2, 0), (w//2, h), (100, 100, 100), 2)
        cv2.line(img, (0, h//2), (w, h//2), (100, 100, 100), 2)

        # 슬라이더 UI 정보 (좌표 및 연결 변수)
        sliders = [
            {"name": "VOL", "x": int(w*0.1), "y_top": int(h*0.1), "y_bot": int(h*0.4), "val": "vol_L"},
            {"name": "ECHO", "x": int(w*0.25), "y_top": int(h*0.1), "y_bot": int(h*0.4), "val": "echo_L"},
            {"name": "TIME", "x": int(w*0.4), "y_top": int(h*0.1), "y_bot": int(h*0.4), "val": "time_L"},
            {"name": "VOL", "x": int(w*0.6), "y_top": int(h*0.1), "y_bot": int(h*0.4), "val": "vol_R"},
            {"name": "ECHO", "x": int(w*0.75), "y_top": int(h*0.1), "y_bot": int(h*0.4), "val": "echo_R"},
            {"name": "TIME", "x": int(w*0.9), "y_top": int(h*0.1), "y_bot": int(h*0.4), "val": "time_R"}
        ]
        
        # 크로스페이더 (가로 슬라이더, 하단 중앙)
        cross_x_left = int(w*0.3)
        cross_x_right = int(w*0.7)
        cross_y = int(h*0.85)

        # 손가락 터치로 슬라이더 조절
        for fx, fy in finger_pos:
            # 수직 슬라이더 처리
            for s in sliders:
                if abs(fx - s["x"]) < 30 and s["y_top"] <= fy <= s["y_bot"]:
                    # Y좌표를 0.0 ~ 1.0 비율로 변환 (위가 1.0)
                    new_val = 1.0 - (fy - s["y_top"]) / (s["y_bot"] - s["y_top"])
                    dj_state[s["val"]] = max(0.0, min(1.0, new_val))
            
            # 수평 크로스페이더 처리
            if cross_x_left <= fx <= cross_x_right and abs(fy - cross_y) < 30:
                new_val = (fx - cross_x_left) / (cross_x_right - cross_x_left)
                dj_state["crossfader"] = max(0.0, min(1.0, new_val))

        # 슬라이더 그리기
        for s in sliders:
            cv2.line(img, (s["x"], s["y_top"]), (s["x"], s["y_bot"]), (50, 50, 50), 4)
            current_y = int(s["y_bot"] - dj_state[s["val"]] * (s["y_bot"] - s["y_top"]))
            cv2.circle(img, (s["x"], current_y), 15, (0, 255, 255), -1)
            img = draw_text_kor(img, s["name"], (s["x"]-20, s["y_bot"]+15), font, (200, 200, 200))

        # 크로스페이더 그리기
        cv2.line(img, (cross_x_left, cross_y), (cross_x_right, cross_y), (50, 50, 50), 6)
        cross_cx = int(cross_x_left + dj_state["crossfader"] * (cross_x_right - cross_x_left))
        cv2.circle(img, (cross_cx, cross_y), 20, (255, 0, 255), -1)
        img = draw_text_kor(img, "CROSSFADER", (w//2 - 50, cross_y + 30), font, (255, 255, 255))

        # 원판 (턴테이블) 그리기 및 회전
        radius = int(h*0.15)
        # 왼쪽 원판
        center_L = (int(w*0.25), int(h*0.7))
        dj_state["spin_L"] = (dj_state["spin_L"] + 2) % 360
        cv2.circle(img, center_L, radius, (30, 30, 30), -1)
        lx = int(center_L[0] + radius * math.cos(math.radians(dj_state["spin_L"])))
        ly = int(center_L[1] + radius * math.sin(math.radians(dj_state["spin_L"])))
        cv2.line(img, center_L, (lx, ly), (0, 255, 0), 3)
        
        # 오른쪽 원판
        center_R = (int(w*0.75), int(h*0.7))
        dj_state["spin_R"] = (dj_state["spin_R"] + 2) % 360
        cv2.circle(img, center_R, radius, (30, 30, 30), -1)
        rx = int(center_R[0] + radius * math.cos(math.radians(dj_state["spin_R"])))
        ry = int(center_R[1] + radius * math.sin(math.radians(dj_state["spin_R"])))
        cv2.line(img, center_R, (rx, ry), (0, 255, 0), 3)

        # 오디오 볼륨 실시간 업데이트 로직 (크로스페이더 반영)
        # 크로스페이더 0.5가 중앙. 0.0이면 왼쪽 100%, 오른쪽 0%.
        cross_vol_L = min(1.0, (1.0 - dj_state["crossfader"]) * 2)
        cross_vol_R = min(1.0, dj_state["crossfader"] * 2)
        
        final_vol_L = dj_state["vol_L"] * cross_vol_L
        final_vol_R = dj_state["vol_R"] * cross_vol_R
        
        if dj_state["left_ch"]: dj_state["left_ch"].set_volume(final_vol_L)
        if dj_state["right_ch"]: dj_state["right_ch"].set_volume(final_vol_R)

    return img

# ==========================================
# 미디어파이프 및 메인 카메라 설정
# ==========================================
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

latest_result = None
def result_callback(result, output_image, timestamp_ms):
    global latest_result
    latest_result = result

options = HandLandmarkerOptions(base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
                                running_mode=VisionRunningMode.LIVE_STREAM,
                                result_callback=result_callback, num_hands=2)

cap = cv2.VideoCapture(0)
window_name = 'Air Master - Pro DJ'
cv2.namedWindow(window_name)
cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

with HandLandmarker.create_from_options(options) as landmarker:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        landmarker.detect_async(mp_image, int(time.time() * 1000))

        update_visual_effects() 
        canvas.delete("aim_dot") 

        finger_positions = []
        fist_count = 0

        if latest_result and latest_result.hand_landmarks:
            for idx, landmarks in enumerate(latest_result.hand_landmarks):
                # 시각화 (뼈대 유지)
                for conn in HAND_CONNECTIONS:
                    cv2.line(frame, (int(landmarks[conn[0]].x*w), int(landmarks[conn[0]].y*h)), 
                             (int(landmarks[conn[1]].x*w), int(landmarks[conn[1]].y*h)), (255,255,255), 1)
                for lm in landmarks: cv2.circle(frame, (int(lm.x*w), int(lm.y*h)), 3, (0, 255, 0), -1)

                if math.sqrt((landmarks[8].x - landmarks[5].x)**2 + (landmarks[8].y - landmarks[5].y)**2) < 0.06: fist_count += 1

                ix, iy = int(landmarks[8].x * w), int(landmarks[8].y * h)
                finger_positions.append((ix, iy))
                is_pinched = math.sqrt((landmarks[12].x-landmarks[4].x)**2 + (landmarks[12].y-landmarks[4].y)**2) < 0.05

                # [모드 공통] FUNNY 모드 진입/해제
                dist_8_5 = math.sqrt((landmarks[8].x - landmarks[5].x)**2 + (landmarks[8].y - landmarks[5].y)**2)
                is_index_folded = dist_8_5 < 0.05
                is_middle_open = landmarks[12].y < landmarks[10].y
                is_others_open = is_middle_open and landmarks[16].y < landmarks[14].y and landmarks[20].y < landmarks[18].y
                
                if is_index_folded and is_others_open and not dj_mode:
                    if time.time() - last_action_time > 1.5:
                        funny_mode = not funny_mode
                        typing_mode = False 
                        if not funny_mode:
                            canvas.delete("crack")
                            selected_concept = None
                        last_action_time = time.time()

                # [바탕화면 파괴 & 레이저]
                is_index_open = landmarks[8].y < landmarks[6].y
                is_ring_folded = landmarks[16].y > landmarks[14].y
                is_pinky_folded = landmarks[20].y > landmarks[18].y

                if funny_mode and selected_concept in ["바탕화면 파괴", "레이저"] and idx == 0:
                    target_tx = np.interp(landmarks[8].x, [0.2, 0.8], [0, sw])
                    target_ty = np.interp(landmarks[8].y, [0.2, 0.8], [0, sh])
                    cx = prev_x + (target_tx - prev_x) * smooth_factor
                    cy = prev_y + (target_ty - prev_y) * smooth_factor
                    cx, cy = max(0, min(sw, cx)), max(0, min(sh, cy))
                    
                    canvas.create_oval(cx-6, cy-6, cx+6, cy+6, fill="red", outline="white", width=2, tags="aim_dot")

                    if selected_concept == "바탕화면 파괴":
                        if is_index_open and is_middle_open and is_ring_folded and is_pinky_folded:
                            if time.time() - last_action_time > 0.8:
                                create_shell_hole(cx, cy)
                                for _ in range(5):
                                    root.geometry(f"+{random.randint(-15,15)}+{random.randint(-15,15)}")
                                    root.update()
                                root.geometry(f"{sw}x{sh}+0+0")
                                last_action_time = time.time()

                    elif selected_concept == "레이저":
                        if is_index_open and not is_middle_open and is_ring_folded and is_pinky_folded:
                            if prev_x != 0 and prev_y != 0:
                                canvas.create_line(prev_x, prev_y, cx, cy, fill="#2b1a10", width=16, capstyle=tk.ROUND, tags="crack")
                                canvas.create_line(prev_x, prev_y, cx, cy, fill="#000000", width=8, capstyle=tk.ROUND, tags="crack")
                                if random.random() > 0.4:
                                    px, py = cx + random.randint(-12, 12), cy + random.randint(-12, 12)
                                    canvas.create_oval(px-3, py-3, px+3, py+3, fill="orange", outline="", tags="crack")
                    prev_x, prev_y = cx, cy

                # [마우스 제어 (노멀 모드)]
                elif not typing_mode and not funny_mode and not dj_mode:
                    if idx == 0:
                        tx = np.interp(landmarks[8].x, [0.2, 0.8], [0, sw])
                        ty = np.interp(landmarks[8].y, [0.2, 0.8], [0, sh])
                        cx = prev_x + (tx - prev_x) * smooth_factor
                        cy = prev_y + (ty - prev_y) * smooth_factor
                        pyautogui.moveTo(cx, cy); prev_x, prev_y = cx, cy
                        if is_pinched: pyautogui.click()
                
                # [가상 키보드 제어]
                elif typing_mode:
                    if is_pinched and time.time() - last_action_time > 0.4:
                        for r, row in enumerate(en_keys):
                            for c, key in enumerate(row):
                                kx, ky = 40 + c*60, 180 + r*60
                                if kx < ix < kx+55 and ky < iy < ky+55:
                                    if key == "lang": pyautogui.press('hangul'); is_hangul_mode = not is_hangul_mode
                                    elif key == "sync": is_hangul_mode = not is_hangul_mode
                                    elif key == "space": pyautogui.press('space')
                                    elif key == "ent": pyautogui.press('enter')
                                    else: pyautogui.keyDown(key); pyautogui.keyUp(key)
                                    last_action_time = time.time()

            # =========================================================
            # [추가] DJ 모드 진입 (양손 엄지 맞대기)
            # =========================================================
            if not funny_mode and not typing_mode and len(latest_result.hand_landmarks) == 2:
                lm1 = latest_result.hand_landmarks[0][4] # 손1 엄지 끝
                lm2 = latest_result.hand_landmarks[1][4] # 손2 엄지 끝
                dist_thumbs = math.sqrt((lm1.x - lm2.x)**2 + (lm1.y - lm2.y)**2)
                
                if dist_thumbs < 0.04 and time.time() - last_action_time > 2.0:
                    dj_mode = not dj_mode
                    if dj_mode:
                        dj_setup = True # 켤 때는 무조건 업로드 창부터
                    else:
                        # DJ 모드 종료 시 음악 정지
                        if dj_state["left_ch"]: dj_state["left_ch"].stop()
                        if dj_state["right_ch"]: dj_state["right_ch"].stop()
                        dj_state["left_path"], dj_state["right_path"] = None, None
                    last_action_time = time.time()

        # [주먹 쥐어서 타이핑 모드 전환]
        if fist_count >= 2 and time.time() - last_action_time > 1.2 and not dj_mode:
            typing_mode = not typing_mode
            funny_mode = False 
            canvas.delete("crack") 
            selected_concept = None
            last_action_time = time.time()

        # UI 출력 라우팅
        if dj_mode:
            frame = process_dj_mode(frame, finger_positions)
        elif typing_mode: 
            frame = draw_keyboard(frame, finger_positions)
        elif funny_mode:
            frame, sel_idx = draw_funny_menu(frame, finger_positions)
            if sel_idx != -1 and latest_result and latest_result.hand_landmarks:
                lms = latest_result.hand_landmarks[0]
                dist_click = math.sqrt((lms[12].x - lms[4].x)**2 + (lms[12].y - lms[4].y)**2)
                if dist_click < 0.05 and time.time() - last_action_time > 0.5:
                    selected_concept = funny_concepts[sel_idx]
                    last_action_time = time.time()
            cv2.putText(frame, f"MODE: FUNNY ({selected_concept})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        else:
            cv2.putText(frame, "MODE: NORMAL", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow(window_name, frame)
        root.update() 
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        if key == ord('c'): canvas.delete("crack")

cap.release()
cv2.destroyAllWindows()
root.destroy()
pygame.mixer.quit()
