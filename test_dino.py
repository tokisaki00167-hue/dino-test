from playwright.sync_api import sync_playwright
import time

def run_dino_ai_stable():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        page.goto("https://chromedino.com/")

        print("已開啟 Dino 遊戲，3 秒後自動開始...")
        time.sleep(3)
        page.keyboard.press("Space")  # 開始遊戲

        start_time = time.time()
        game_duration = 60
        last_jump = 0
        base_distance = 80
        speed_factor = 0.9
        merge_gap = 10
        extreme_gap_threshold = 10  # 距離小於 10 就視為極端事件

        # ✅ 極端事件計數器
        extreme_event_count = 0
        # ✅ 冷卻時間 (避免重複計數同一障礙物)
        last_extreme_time = 0
        extreme_cooldown = 0.5  # 單位：秒

        while time.time() - start_time < game_duration:
            try:
                # 抓取 Dino 與障礙物狀態
                result = page.evaluate("""
                    (() => {
                        const tRex = Runner.instance_.tRex;
                        const obstacles = Runner.instance_.horizon.obstacles || [];
                        const speed = Runner.instance_.currentSpeed;
                        const crashed = Runner.instance_.crashed;
                        return {
                            obstacles: obstacles.map(o => ({
                                x: o.xPos || 0,
                                w: o.width || 0,
                                y: o.yPos || 0,
                                h: o.height || 0
                            })),
                            tRexX: tRex.xPos,
                            speed: speed,
                            crashed: crashed
                        };
                    })()
                """)

                obstacles = result['obstacles']
                tRexX = result['tRexX']
                speed = result['speed']
                crashed = result['crashed']

                # ✅ 若 Dino 撞到障礙物，自動重啟遊戲
                if crashed:
                    print("\n💥 Dino 撞到障礙物，重新開始...")
                    page.keyboard.press("Space")  # 重啟遊戲
                    time.sleep(0.5)
                    continue

                jump_threshold = base_distance + speed * speed_factor
                jump_trigger = False

                # 合併黏在一起的障礙物
                merged_obstacles = []
                obstacles_sorted = sorted(obstacles, key=lambda o: o['x'])
                for obs in obstacles_sorted:
                    if not merged_obstacles:
                        merged_obstacles.append(obs)
                    else:
                        last = merged_obstacles[-1]
                        if obs['x'] - (last['x'] + last['w']) <= merge_gap:
                            last['w'] = max(last['w'], obs['x'] + obs['w'] - last['x'])
                        else:
                            merged_obstacles.append(obs)

                # 找最近障礙物（✅ 修正：只考慮前方）
                closest_obs = None
                closest_dist = None
                for obs in merged_obstacles:
                    distance = obs['x'] - tRexX
                    if distance > 0:  # ✅ 只考慮恐龍前方的障礙物
                        if closest_dist is None or distance < closest_dist:
                            closest_dist = distance
                            closest_obs = obs
                        if distance < jump_threshold and time.time() - last_jump > 0.1:
                            jump_trigger = True

                # 執行跳躍
                if jump_trigger:
                    page.keyboard.press("Space")
                    last_jump = time.time()

                    # ✅ 僅在 Dino 起跳時判定是否為極端事件
                    if (closest_dist is not None and closest_dist < extreme_gap_threshold and
                        time.time() - last_extreme_time > extreme_cooldown):
                        extreme_event_count += 1
                        last_extreme_time = time.time()
                        print(f"\n⚠️ 極端事件觸發！距離: {closest_dist:.2f}")



                # 終端顯示
                print(f"Speed: {speed:.2f}, Jump threshold: {jump_threshold:.2f}, "
                      f"Distance to obs: {closest_dist}", end='\r')

            except Exception:
                print("偵測障礙物小錯誤，略過", end='\r')

            time.sleep(0.02)

        # ✅ 遊戲結束後輸出統計
        print("\n===== 遊戲結束 =====")
        print(f"極端事件觸發次數: {extreme_event_count}")

        input("按 Enter 關閉視窗...")
        browser.close()

if __name__ == "__main__":
    run_dino_ai_stable()
