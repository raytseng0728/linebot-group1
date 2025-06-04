from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent,
    ImageComponent, PostbackAction
)

def send_flex_menu(user_id):
    def image_card(title, image_url, action_data):
        return BoxComponent(
            layout="vertical",
            padding_all="sm",
            corner_radius="md",
            border_width="medium",
            border_color="#cccccc",
            background_color="#ffffff",
            action=PostbackAction(label=title, data=action_data),
            contents=[
                ImageComponent(
                    url=image_url,
                    size="full",
                    aspect_ratio="1:1",
                    aspect_mode="cover",
                    animated=True
                )
            ],
            flex=1
        )

    # 使用靜態完成率圖片（固定）
    pie_chart_url = "https://i.postimg.cc/gcMZ5fNW/2.png"

    bubble = BubbleContainer(
        direction="ltr",
        body=BoxComponent(
            layout="vertical",
            contents=[
                # 第一排按鈕
                BoxComponent(
                    layout="horizontal",
                    spacing="sm",
                    contents=[
                        image_card("開始學習", "https://i.postimg.cc/1Rbh5zz5/tile-0-0.png", "action=start"),
                        image_card("單字庫複習", "https://i.postimg.cc/RVfr3z31/tile-0-1.png", "action=review"),
                        image_card("新單字學習", "https://i.postimg.cc/L4cwF0yJ/tile-0-2.png", "action=learn")
                    ]
                ),
                # 第二排按鈕（含圓餅圖）
                BoxComponent(
                    layout="horizontal",
                    spacing="sm",
                    margin="md",
                    contents=[
                        image_card("說明", "https://i.postimg.cc/GtSTyyH2/1.png", "action=help"),
                        image_card("單字小考", "https://i.postimg.cc/YSCyxcSs/tile-1-1.png", "action=quiz"),
                        image_card("完成率", pie_chart_url, "action=progress")
                    ]
                )
            ]
        )
    )

    return FlexSendMessage(
        alt_text="單字機器人選單",
        contents=bubble
    )
