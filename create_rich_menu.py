from linebot import LineBotApi
from linebot.models import RichMenu, RichMenuArea, RichMenuBounds, URIAction, MessageAction
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))

# 建立 Rich Menu
rich_menu_to_create = RichMenu(
    size={"width": 2500, "height": 843},
    selected=True,
    name="Main Menu",
    chat_bar_text="開啟選單",
    areas=[
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=0, width=625, height=843),
            action=MessageAction(label="複習", text="我要複習")
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=625, y=0, width=625, height=843),
            action=MessageAction(label="學習", text="我要學習")
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=1250, y=0, width=625, height=843),
            action=MessageAction(label="小考", text="我要測驗")
        ),
        
        RichMenuArea(
            bounds=RichMenuBounds(x=1875, y=0, width=625, height=843),
            action=MessageAction(label="完成率", text="我要看完成率")
        ),
    ]
)

# 建立並上傳圖片
rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu_to_create)

with open("richmenu.jpg", "rb") as image_file:
    line_bot_api.set_rich_menu_image(rich_menu_id, "image/jpeg", image_file)

# 綁定給所有使用者
line_bot_api.set_default_rich_menu(rich_menu_id)

print("Rich menu 已建立並設定為預設")
