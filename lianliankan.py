import sys
import time
import random
import msvcrt
from PIL import ImageGrab, Image
import numpy as np
import win32gui
import win32api
import win32con

############################## 全局参数 ##############################
window_title = "QQ游戏 - 连连看角色版"
game_width = 589
game_height = 385
num_row = 11
num_col = 19
grid_width = 31
grid_height = 35
color_empty_grid = (48, 76, 112)

# 点击速度参数（可从命令行传入）
click_delay = 0.1  # 默认点击间隔（秒）
round_delay = 0.5  # 默认轮次间隔（秒）

# 全局停止标志
stop_program = False

def check_stop_condition():
    """检查停止条件 - 检查ESC键和游戏窗口"""
    global stop_program
    
    # 检查ESC键
    if msvcrt.kbhit():
        key = msvcrt.getch()
        if key == b'\x1b':  # ESC键
            print("\n检测到ESC键，正在停止程序...")
            stop_program = True
            return True
    
    # 检查游戏窗口
    hwnd = win32gui.FindWindow(0, window_title)
    if hwnd == 0:
        print("游戏窗口已关闭，停止程序")
        stop_program = True
        return True
    
    return stop_program

def isEmptyGrid(img):
    """检查是否为空格子"""
    center_img = img.resize((img.width // 8, img.height // 8),
                         box=(img.width // 8 * 3, img.height // 8 * 3,
                              img.width // 8 * 5, img.height // 8 * 5))
    
    for pixel in center_img.getdata():
        if pixel != color_empty_grid:
            return False
    return True

def getGameImage():
    """截取游戏区域图片"""
    global game_left, game_top, game_right, game_bottom
    try:
        size = (game_left, game_top, game_right, game_bottom)
        img = ImageGrab.grab(size)
        return img
    except Exception as e:
        print("截图错误:", e)
        return None

def gameImageToMatrix(img):
    """将游戏图片转换为矩阵"""
    image_matrix = {}
    unknown_type_image = []
    
    for row in range(num_row):
        image_matrix[row] = {}
        for col in range(num_col):
            left = col * grid_width
            top = row * grid_height
            right = left + grid_width
            bottom = top + grid_height
            
            grid_image = img.crop((left, top, right, bottom))
            image_matrix[row][col] = grid_image
    
    # 生成矩阵ID
    image_matrix_id = {}
    for row in range(num_row):
        image_matrix_id[row] = {}
        for col in range(num_col):
            this_img = image_matrix[row][col]
            if isEmptyGrid(this_img):
                image_matrix_id[row][col] = 0
                continue
            
            found = False
            for i in range(len(unknown_type_image)):
                if isSameGrid(this_img, unknown_type_image[i]):
                    found = True
                    image_matrix_id[row][col] = i + 1
                    break
            
            if not found:
                unknown_type_image.append(this_img)
                image_matrix_id[row][col] = len(unknown_type_image)
    
    return image_matrix_id

def isSameGrid(img_a, img_b):
    """使用直方图相似度判断方块是否相同"""
    if img_a.size != img_b.size:
        return False
    
    array_a = np.array(img_a)
    array_b = np.array(img_b)
    return classify_hist_with_split(array_a, array_b, img_a.size) > 0.95

def classify_hist_with_split(image1, image2, size=(256, 256)):
    """计算RGB三通道直方图相似度"""
    # 调整图像大小
    if image1.shape[:2] != size:
        h, w = image1.shape[:2]
        new_h, new_w = size
        
        if h <= new_h or w <= new_w:
            pass
        else:
            step_h = max(1, h // new_h)
            step_w = max(1, w // new_w)
            image1 = image1[::step_h, ::step_w][:new_h, :new_w]
            image2 = image2[::step_h, ::step_w][:new_h, :new_w]
    
    # 分离RGB通道
    if len(image1.shape) == 3:
        channels1 = [image1[:,:,i] for i in range(3)]
        channels2 = [image2[:,:,i] for i in range(3)]
    else:
        channels1 = [image1]
        channels2 = [image2]
    
    # 计算每个通道的相似度
    total_similarity = 0
    for ch1, ch2 in zip(channels1, channels2):
        hist1, _ = np.histogram(ch1, bins=256, range=(0, 256))
        hist2, _ = np.histogram(ch2, bins=256, range=(0, 256))
        
        similarity = 0
        for i in range(len(hist1)):
            if hist1[i] != hist2[i]:
                max_val = max(hist1[i], hist2[i])
                if max_val > 0:
                    similarity += 1 - abs(hist1[i] - hist2[i]) / max_val
                else:
                    similarity += 1
            else:
                similarity += 1
        
        total_similarity += similarity / len(hist1)
    
    return total_similarity / len(channels1)

def verifying_connectivity(matrix, x1, y1, x2, y2):
    """连通性检查 - 使用BFS算法"""
    global stop_program
    if stop_program:
        return False
        
    if matrix[y1][x1] != matrix[y2][x2]:
        return False
    
    return bfs_connectivity(matrix, x1, y1, x2, y2)

def bfs_connectivity(matrix, x1, y1, x2, y2):
    """BFS搜索连通路径，最多两次转向"""
    global stop_program
    
    if stop_program:
        return False
    
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    queue = [(x1, y1, -1, 0, [(x1, y1)])]
    visited = set()
    
    while queue and not stop_program:
        x, y, direction, turns, path = queue.pop(0)
        
        if x == x2 and y == y2:
            return True
        
        if turns > 2:
            continue
        
        state = (x, y, direction, turns)
        if state in visited:
            continue
        visited.add(state)
        
        for i, (dx, dy) in enumerate(directions):
            nx, ny = x + dx, y + dy
            
            if nx < 0 or nx >= num_col or ny < 0 or ny >= num_row:
                continue
            
            if (nx, ny) == (x1, y1) and len(path) > 1:
                continue
            
            if matrix[ny][nx] != 0 and not (nx == x2 and ny == y2):
                continue
            
            new_turns = turns
            if direction != -1 and direction != i:
                new_turns += 1
            
            if new_turns <= 2:
                new_path = path + [(nx, ny)]
                queue.append((nx, ny, i, new_turns, new_path))
    
    return False

def mouseClick(x, y):
    """快速鼠标点击"""
    int_x = int(x)
    int_y = int(y)
    win32api.SetCursorPos((int_x, int_y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, int_x, int_y, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, int_x, int_y, 0, 0)

def solve(matrix, hwnd):
    """主求解函数"""
    global game_left, game_top, click_delay, round_delay
    
    if check_stop_condition():
        return
    
    # 统计剩余方块
    remaining_blocks = 0
    block_positions = {}
    
    for row in range(num_row):
        for col in range(num_col):
            if matrix[row][col] != 0:
                remaining_blocks += 1
                block_type = matrix[row][col]
                if block_type not in block_positions:
                    block_positions[block_type] = []
                block_positions[block_type].append((col, row))
    
    print(f"剩余方块数量: {remaining_blocks}")
    if remaining_blocks == 0:
        print("游戏完成！")
        return
    
    # 找到可消除配对
    execution_queue = []
    for block_type, positions in block_positions.items():
        if stop_program:
            break
            
        for idx1 in range(len(positions) - 1):
            x1, y1 = positions[idx1]
            for idx2 in range(idx1 + 1, len(positions)):
                x2, y2 = positions[idx2]
                if stop_program:
                    break
                    
                if verifying_connectivity(matrix, x1, y1, x2, y2):
                    execution_queue.append((y1, x1, y2, x2))
    
    print(f"找到 {len(execution_queue)} 个可消除配对")
    
    if not execution_queue:
        print("没有找到可消除的配对")
        return
    
    # 执行点击
    eliminated_this_round = 0
    successful_clicks = 0
    
    for from_row, from_col, to_row, to_col in execution_queue[:20]:
        if stop_program:
            break
            
        if matrix[from_row][from_col] == 0 or matrix[to_row][to_col] == 0:
            continue
        
        # 计算点击坐标
        from_x = game_left + from_col * grid_width + grid_width // 2
        from_y = game_top + from_row * grid_height + grid_height // 2
        to_x = game_left + to_col * grid_width + grid_width // 2
        to_y = game_top + to_row * grid_height + grid_height // 2
        
        print(f"点击: ({from_col}, {from_row}) -> ({to_col}, {to_row})")
        
        # 执行点击
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.02)
        
        mouseClick(from_x, from_y)
        time.sleep(click_delay)
        mouseClick(to_x, to_y)
        time.sleep(click_delay)
        
        # 更新矩阵
        matrix[from_row][from_col] = 0
        matrix[to_row][to_col] = 0
        eliminated_this_round += 2
        successful_clicks += 1
        
        if successful_clicks >= 10:
            break
    
    print(f"本轮消除了 {eliminated_this_round} 个方块")
    
    # 继续下一轮
    if eliminated_this_round > 0 and not stop_program:
        print("继续下一轮...")
        time.sleep(round_delay)
        solve(matrix, hwnd)
    else:
        print("本轮无进展或程序停止")

def start():
    """启动函数"""
    global game_left, game_top, game_right, game_bottom
    
    hwnd = win32gui.FindWindow(0, window_title)
    if hwnd == 0:
        print("未找到游戏窗口，请确保QQ连连看已启动")
        return
    
    print(f"找到游戏窗口句柄: {hwnd}")
    
    # 激活窗口
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(1)
    
    window_left, window_top, window_right, window_bottom = win32gui.GetWindowRect(hwnd)
    print(f"窗口坐标: ({window_left}, {window_top}) - ({window_right}, {window_bottom})")
    
    # 计算游戏区域
    actual_window_width = window_right - window_left
    actual_window_height = window_bottom - window_top
    
    game_left = window_left + int(14.0 / 800.0 * actual_window_width)
    game_top = window_top + int(181.0 / 600.0 * actual_window_height)
    game_right = game_left + game_width
    game_bottom = game_top + game_height
    
    print(f"游戏区域: ({game_left}, {game_top}) - ({game_right}, {game_bottom})")
    
    # 截图并转换矩阵
    img = getGameImage()
    if img:
        print(f"成功截取游戏区域图片，大小: {img.size}")
        matrix = gameImageToMatrix(img)
        solve(matrix, hwnd)
    else:
        print("截图失败")

if __name__ == '__main__':
    print("连连看自动化脚本启动...")
    print("提示：按ESC键可停止程序")
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        try:
            speed = float(sys.argv[1])
            if 0.01 <= speed <= 2.0:
                click_delay = speed
                round_delay = speed * 5  # 轮次间隔为点击间隔的5倍
                print(f"设置点击速度: {click_delay}秒")
            else:
                print("速度参数应在0.01-2.0之间，使用默认值")
        except ValueError:
            print("无效的速度参数，使用默认值")
    
    start()
