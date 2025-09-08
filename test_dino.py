from playwright.sync_api import sync_playwright
import time

def run_dino_ai_with_extreme_detection():
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
        base_distance = 90   # 你的設定
        speed_factor = 4      # 你的設定
        merge_gap = 10
        extreme_gap_threshold = 60  # 低於這距離的障礙物，視為極端事件
        extreme_events = []

        while time.time() - start_time < game_duration:
            try:
                result = page.evaluate("""
                    (() => {
                        const tRex = Runner.instance_.tRex;
                        const obstacles = Runner.instance_.horizon.obstacles || [];
                        const speed = Runner.instance_.currentSpeed;
                        return {
                            obstacles: obstacles.map(o => ({
                                x: o.xPos || 0,
                                w: o.width || 0,
                                y: o.yPos || 0,
                                h: o.height || 0
                            })),
                            tRexX: tRex.xPos,
                            speed: speed
                        };
                    })()
                """)

                obstacles = result['obstacles']
                tRexX = result['tRexX']
                speed = result['speed']

                jump_threshold = base_distance + speed * speed_factor
                jump_trigger = False

                # 合併黏在一起的障礙物群
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

                closest_obs = None
                closest_dist = None
                for i, obs in enumerate(merged_obstacles):
                    distance = obs['x'] - tRexX

                    # 檢測極端事件（與下一個障礙物距離太近）
                    if i < len(merged_obstacles) - 1:
                        next_obs = merged_obstacles[i + 1]
                        gap = next_obs['x'] - (obs['x'] + obs['w'])
                        if 0 < gap < extreme_gap_threshold:
                            event_time = round(time.time() - start_time, 2)
                            extreme_events.append((event_time, gap))
                            print(f"\n⚠️ Extreme case detected at {event_time}s, gap={gap}")

                    if closest_dist is None or distance < closest_dist:
                        closest_dist = distance
                        closest_obs = obs
                    if distance < jump_threshold and time.time() - last_jump > 0.1:
                        jump_trigger = True

                if jump_trigger:
                    page.keyboard.press("Space")
                    last_jump = time.time()

                # 畫紅線標記最近障礙物
                if closest_obs:
                    obs_w = max(closest_obs['w'], 1)
                    obs_h = max(closest_obs['h'], 1)
                    page.evaluate(f"""
                        (() => {{
                            const canvas = document.querySelector('canvas');
                            const ctx = canvas.getContext('2d');
                            ctx.strokeStyle = 'red';
                            ctx.lineWidth = 2;
                            ctx.beginPath();
                            ctx.rect({closest_obs['x']}, {closest_obs['y']}, {obs_w}, {obs_h});
                            ctx.stroke();
                        }})()
                    """)

                # 終端顯示
                print(f"Speed: {speed:.2f}, Jump threshold: {jump_threshold:.2f}, Distance to obs: {closest_dist}", end='\r')

            except Exception:
                print("偵測障礙物小錯誤，略過", end='\r')

            time.sleep(0.02)

        print("\n\n=== 遊戲結束 ===")
        if extreme_events:
            print("偵測到的極端事件：")
            for t, g in extreme_events:
                print(f"  - {t}s 時，障礙間距 = {g}")
        else:
            print("沒有偵測到極端事件")

        input("按 Enter 關閉視窗...")
        browser.close()

if __name__ == "__main__":
    run_dino_ai_with_extreme_detection()
