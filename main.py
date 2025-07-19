import pygame
from openai import OpenAI
import sys
from dotenv import load_dotenv
import os
from pygame.locals import *

# show Chinese IME UI
os.environ["SDL_IME_SHOW_UI"] = "1"

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_api_endpoint = os.getenv("OPENAI_API_ENDPOINT")

# 初始化pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("简易NPC对话Demo")
font = pygame.font.SysFont("simhei", 24)
clock = pygame.time.Clock()

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

client = OpenAI(api_key=openai_api_key,
                base_url=openai_api_endpoint)


class Character:
    def __init__(self, name, x, y, color, prompt):
        self.name = name
        self.x = x
        self.y = y
        self.color = color
        self.prompt = prompt
        self.radius = 20
        self.conversation = []

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius)
        name_text = font.render(self.name, True, BLACK)
        surface.blit(
            name_text, (self.x - name_text.get_width()//2, self.y - 30))

    def get_ai_response(self, player_input):
        """获取AI生成的NPC回复"""

        messages = [{"role": "system", "content": self.prompt}]
        messages.extend(self.conversation)
        messages.append({"role": "user", "content": player_input})

        try:
            print(f"{self.name} 正在处理输入: {player_input}")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=50,
            )
            reply = response.choices[0].message.content
            print(f"{self.name} 回复: {reply}")
            self.conversation.append(
                {"role": "user", "content": player_input})
            self.conversation.append(
                {"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            print(f"Error fetching AI response: {e}")
            return "（NPC暂时无法回应）"


# 创建角色
player = Character("玩家", 400, 500, GREEN, "")
npc1 = Character("铁匠", 200, 300, BLUE, "你是一个中世纪的铁匠，说话简洁直接，回答不超过2句话。")
npc2 = Character("巫师", 600, 300, RED, "你是一个神秘的巫师，说话充满谜语和隐喻，回答不超过2句话。")

# 游戏状态
current_speaker = None
player_input = ""
dialogue_active = False
dialogue_history = []
input_active = False
input_rect = None


def draw_dialogue_box():
    """绘制对话界面"""
    if not dialogue_active:
        return

    s = pygame.Surface((800, 200))
    s.set_alpha(200)
    s.fill(WHITE)
    screen.blit(s, (0, 400))

    # 绘制历史对话
    y_offset = 410
    # 计算历史对话需要的总高度
    history_height = len(dialogue_history[-3:]) * 30  # 每行 30 像素
    y_offset = 470 - history_height  # 输入框在 470，历史对话在其上方

    # 绘制历史对话
    for i, (speaker, text) in enumerate(dialogue_history[-3:]):
        dialogue_text = font.render(f"{speaker}: {text}", True, BLACK)
        screen.blit(dialogue_text, (10, y_offset + i * 30))

    # 绘制输入框
    input_box_color = BLUE if input_active else BLACK  # 激活时变蓝色
    input_rect = pygame.draw.rect(
        screen, input_box_color, (10, 470, 780, 30), 2)
    pygame.key.set_text_input_rect(input_rect)
    pygame.key.start_text_input()  # 必须调用
    input_text = font.render(player_input, True, BLACK)
    screen.blit(input_text, (15, 475))

    # 绘制提示
    prompt = font.render("按回车发送，ESC退出对话", True, BLACK)
    screen.blit(prompt, (500, 475))


# 主游戏循环
running = True
while running:
    screen.fill(WHITE)

    player.draw(screen)
    npc1.draw(screen)
    npc2.draw(screen)

    draw_dialogue_box()

    if not dialogue_active:
        prompt = font.render("靠近NPC按空格键开始对话", True, BLACK)
        screen.blit(prompt, (300, 550))

    pygame.display.flip()
    clock.tick(30)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # 鼠标点击事件 - 激活/取消激活输入框
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if dialogue_active:
                input_box_rect = pygame.Rect(10, 470, 780, 30)
                if input_box_rect.collidepoint(event.pos):
                    print("输入框被点击")
                    input_active = True
                else:
                    print
                    input_active = False

        # 键盘输入处理
        # elif event.type == pygame.TEXTEDITING:
        #     print('English text editing')
        #     print(event)  # 打印事件信息，便于调试
        #     if dialogue_active and input_active:
        #         player_input = event.text
        elif event.type == pygame.KEYDOWN:
            print('keydown')
            print(event)
            if dialogue_active and input_active:
                if event.key == pygame.K_ESCAPE:
                    print('ESC pressed')
                    dialogue_active = False
                    player_input = ""
                    input_active = False

                elif event.key == pygame.K_BACKSPACE:
                    player_input = player_input[:-1]

                else:
                    # 只添加可打印字符
                    if event.unicode.isprintable():
                        player_input += event.unicode
            elif event.key == pygame.K_SPACE and not dialogue_active:
                print('space pressed')
                # 检测与NPC的距离
                player_rect = pygame.Rect(player.x - player.radius, player.y - player.radius,
                                          player.radius*2, player.radius*2)

                for npc in [npc1, npc2]:
                    npc_rect = pygame.Rect(npc.x - npc.radius, npc.y - npc.radius,
                                           npc.radius*2, npc.radius*2)

                    if player_rect.colliderect(npc_rect):
                        current_speaker = npc
                        dialogue_active = True
                        input_active = True  # 自动激活输入框
                        dialogue_history.append((npc.name, "（按ESC键结束对话）"))
                        break
        elif event.type == pygame.KEYUP and dialogue_active:
            print('keyup')
            print(event)
            if (player_input and event.key == pygame.K_RETURN):
                # 发送玩家输入
                print(f"玩家输入: {player_input}")
                if current_speaker:
                    print(f"当前NPC: {current_speaker.name}")
                    response = current_speaker.get_ai_response(player_input)
                    dialogue_history.append((current_speaker.name, response))
                    player_input = ""
            # 在游戏循环中添加
        elif event.type == pygame.TEXTINPUT:
            print('Chinese text input')
            print(event)
            if dialogue_active and input_active:
                player_input += event.text

    # 玩家移动
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player.x -= 5
    if keys[pygame.K_RIGHT]:
        player.x += 5
    if keys[pygame.K_UP]:
        player.y -= 5
    if keys[pygame.K_DOWN]:
        player.y += 5

pygame.quit()
sys.exit()
