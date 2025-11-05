import gradio as gr
import io
from PIL import Image
from core.vto_service.gemini_handler import GeminiProcesser
from core.litellm_hander.schema import ModelOptions, ClothesOptions
from prompts.vto_model_prompts import assemble_model_prompt
from prompts.vto_prompts import assemble_prompt
from prompts.prod_image_prompts import product_image_prompt
from prompts.side_view_prompts import side_view_prompt
from core.litellm_hander.utils import (
    gender_options, fit_options, sleeve_options, length_options, clothes_category,
    skin_tone_options, ethnicity_options, hairstyle_options, age_options, hair_color_options
)

async def process_inputs(text_input, image1, image2, image3, temperature, top_p, num_images, aspect_ratio):
    """
    텍스트 입력과 이미지 입력들을 처리하는 함수
    """
    gemini_processer = GeminiProcesser(verbose=True)
    
    # 콘텐츠 생성 (이미지를 미리 변환)
    contents_list = [text_input]
    if image1 is not None:
        contents_list.append(await gemini_processer.create_image_content(image1))
    if image2 is not None:
        contents_list.append(await gemini_processer.create_image_content(image2))
    if image3 is not None:
        contents_list.append(await gemini_processer.create_image_content(image3))
    
    # VTO 추론 실행
    result = await gemini_processer.execute_image_inference(
        contents_list=contents_list,
        image_count=num_images,
        temperature=temperature,
        top_p=top_p,
        aspect_ratio=aspect_ratio
    )
    
    # response를 bytes 리스트로 가져오기
    response = result.get("response", [])
    
    # bytes 데이터를 PIL Image로 변환
    pil_images = []
    for img_bytes in response:
        if img_bytes is not None:
            pil_images.append(Image.open(io.BytesIO(img_bytes)))
    
    # usage 정보 포맷팅
    usage = result.get("usage")
    usage_text = ""
    if usage:
        usage_text = f"""📊 사용량 정보
━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔹 모델: {usage.model_name}
🔹 작업: {usage.task_name}

📝 토큰 사용량:
    • 입력 토큰: {usage.prompt_token_count:,}
    • 출력 토큰: {usage.candidates_token_count:,}
    • 총 토큰: {usage.total_token_count:,}

💰 비용:
    • USD: ${usage.cost_usd:.6f}
    • KRW: ₩{usage.cost_krw:,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # debug_info 포맷팅
    debug_info = result.get("debug_info", {})
    debug_text = ""
    if debug_info:
        debug_text = f"""🔍 디버그 정보
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📸 생성 결과:
    • 앞면 이미지: {debug_info.get('front_count', 0)}개
    • 뒷면 이미지: {debug_info.get('back_count', 0)}개
    • 측면 이미지: {debug_info.get('side_count', 0)}개
    • 총 이미지: {debug_info.get('total_count', 0)}개

✅ 성공/실패:
    • 성공: {debug_info.get('success_count', 0)}개
    • 실패: {debug_info.get('fail_count', 0)}개

⚙️  요청 정보:
    • 뷰당 요청 개수: {debug_info.get('requested_count_per_view', 0)}개
    • 모델: {debug_info.get('model_name', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    return pil_images, usage_text, debug_text


def update_prompt(main_category, sub_category, replacement, gender, fit, sleeve, length):
    """
    선택된 옵션에 따라 프롬프트를 업데이트하는 함수
    """
    try:
        prompt = assemble_prompt(
            main_category=main_category,
            sub_category=sub_category,
            replacement=replacement,
            gender=gender if gender != "none" else None,
            fit=fit if fit != "none" else None,
            sleeve=sleeve if sleeve != "none" else None,
            length=length if length != "none" else None,
        )
        return prompt
    except Exception as e:
        return f"오류 발생: {str(e)}"


def update_sub_category_choices(main_category, replacement, gender, fit, sleeve, length):
    """
    메인 카테고리에 따라 서브 카테고리 선택지를 업데이트하고 프롬프트도 업데이트하는 함수
    """
    catalog = clothes_category()
    if main_category == "default":
        sub_category_value = "default"
        dropdown_update = gr.update(choices=["default"], value="default")
    elif main_category in catalog:
        sub_cats = catalog[main_category]["children"]
        choices = [(sub_cats[key]["name"], key) for key in sub_cats.keys()]
        sub_category_value = "none"
        dropdown_update = gr.update(choices=choices, value="none")
    else:
        sub_category_value = "none"
        dropdown_update = gr.update(choices=["none"], value="none")
    
    # 프롬프트도 함께 업데이트
    prompt = update_prompt(main_category, sub_category_value, replacement, gender, fit, sleeve, length)
    return dropdown_update, prompt


def update_model_prompt(view_type, gender, age, skin_tone, ethnicity, hairstyle, hair_color, height, weight, main_category, sub_category, sleeve, length, fit, wear_together, total_length):
    """
    선택된 옵션에 따라 모델 프롬프트를 업데이트하는 함수 (Pydantic 모델 사용)
    """
    try:
        # ModelOptions 생성
        model_options = ModelOptions(
            gender=gender,
            age=age if age != "none" else None,
            skin_tone=skin_tone if skin_tone != "none" else None,
            ethnicity=ethnicity if ethnicity != "none" else None,
            hairstyle=hairstyle if hairstyle != "none" else None,
            hair_color=hair_color if hair_color != "none" else None,
            height=height if height is not None and height > 0 else None,
            weight=weight if weight is not None and weight > 0 else None
        )
        
        # ClothesOptions 생성
        # main_category가 "none"이어도 total_length가 있으면 ClothesOptions 생성
        if main_category != "none" or (total_length is not None and total_length > 0):
            clothes_options = ClothesOptions(
                main_category=main_category if main_category != "none" else "none",
                sub_category=sub_category if sub_category != "none" else "none",
                sleeve=sleeve if sleeve != "none" else None,
                length=length if length != "none" else None,
                fit=fit if fit != "none" else None,
                total_length=total_length if total_length is not None and total_length > 0 else None
            )
        else:
            clothes_options = None
        
        # 프롬프트 생성
        prompt = assemble_model_prompt(
            type=view_type,
            model_options=model_options,
            clothes_options=clothes_options,
            wear_together=wear_together if wear_together and wear_together.strip() else None
        )
        return prompt
    except Exception as e:
        return f"오류 발생: {str(e)}"


# Gradio 인터페이스 생성
with gr.Blocks(title="제미나이 실험실") as demo:
    gr.Markdown("# 🔬 제미나이 실험실")
    gr.Markdown("텍스트 입력 1개와 최대 3개의 이미지를 업로드할 수 있습니다.")
    with gr.Tab("🧑‍🔬 실험실"):
        with gr.Row():
            with gr.Column():
                text_input = gr.Textbox(
                    label="텍스트 입력",
                    placeholder="텍스트를 입력하세요...",
                    lines=3
                )
                
            with gr.Column():
                with gr.Row():
                    temperature = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=1.0,
                        step=0.1,
                        label="Temperature",
                        info="생성 모델의 창의성 조절 (낮을수록 일관적, 높을수록 다양함)"
                    )
                    
                    top_p = gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=0.95,
                        step=0.01,
                        label="Top-p (Nucleus Sampling)",
                        info="샘플링 다양성 조절 (낮을수록 보수적, 높을수록 다양함)"
                    )
                with gr.Row():
                    num_images = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=3,
                        step=1,
                        label="생성할 이미지 개수",
                        info="생성할 이미지의 개수를 선택하세요"
                    )
                    
                    aspect_ratio = gr.Dropdown(
                        label="🖼️ 이미지 비율",
                        choices=[
                            ("1:1 (1024*1024)", "1:1"),
                            ("2:3 (832*1248)", "2:3"),
                            ("3:2 (1248*832)", "3:2"),
                            ("3:4 (864*1184)", "3:4"),
                            ("4:3 (1184*864)", "4:3"),
                            ("4:5 (896*1152)", "4:5"),
                            ("5:4 (1152*896)", "5:4"),
                            ("9:16 (768*1344)", "9:16"),
                            ("16:9 (1344*768)", "16:9"),
                            ("21:9 (1536*672)", "21:9")
                        ],
                        value="1:1",
                        info="이미지 비율 선택",
                        interactive=True
                    )
                
                submit_btn = gr.Button("🚀 실행", variant="primary")
        with gr.Row():
            image1 = gr.Image(
                label="이미지 1",
                format="png",
                image_mode="RGB"
            )
            
            image2 = gr.Image(
                label="이미지 2 (선택사항)",
                format="png",
                image_mode="RGB"
            )
            
            image3 = gr.Image(
                label="이미지 3 (선택사항)",
                format="png",
                image_mode="RGB"
            )
            
        with gr.Row():
            output = gr.Gallery(
                label="VTO 결과",
                show_label=False,
                elem_id="output_gallery",
                columns=3,
                object_fit="contain",
                height=700,
                format="png"
            )
        
        with gr.Row():
            with gr.Column():
                usage_output = gr.Textbox(
                    label="💰 사용량 정보",
                    lines=12,
                    interactive=False
                )
            
            with gr.Column():
                debug_output = gr.Textbox(
                    label="🔍 디버그 정보",
                    lines=12,
                    interactive=False
                )
            
        submit_btn.click(
            fn=process_inputs,
            inputs=[text_input, image1, image2, image3, temperature, top_p, num_images, aspect_ratio],
            outputs=[output, usage_output, debug_output]
        )
    
    with gr.Tab("🧑 가상 모델 생성 프롬프트"):
        with gr.Column():
            gr.Markdown("## 가상 모델 생성 프롬프트")
            gr.Markdown("Front View와 Back View 모델 이미지를 생성하기 위한 프롬프트입니다.")
            gr.Markdown("### 옵션 선택")
            
            # 옵션 데이터 준비
            gender_opts = gender_options()
            fit_opts = fit_options()
            sleeve_opts = sleeve_options()
            length_opts = length_options()
            catalog = clothes_category()
            age_opts = age_options()
            skin_opts = skin_tone_options()
            ethnicity_opts = ethnicity_options()
            hair_opts = hairstyle_options()
            hair_color_opts = hair_color_options()
            
            with gr.Row():
                with gr.Column(scale=1):
                    model_view_radio = gr.Radio(
                        label="📷 View",
                        choices=[("Front View", "front"), ("Back View", "back")],
                        value="front",
                        info="앞면 또는 뒷면 선택"
                    )
                    
                    model_gender_radio = gr.Radio(
                        label="👤 성별",
                        choices=[("여성", "woman"), ("남성", "man")],
                        value="woman",
                        info="모델 성별 선택"
                    )
                    
                    model_age_dropdown = gr.Dropdown(
                        label="🎂 나이",
                        choices=[(age_opts[key]["name"], key) for key in age_opts.keys()],
                        value="young",
                        info=age_opts["young"]["desc"]
                    )
                    
                    model_skin_dropdown = gr.Dropdown(
                        label="🎨 피부색",
                        choices=[(skin_opts[key]["name"], key) for key in skin_opts.keys()],
                        value="none",
                        info=skin_opts["none"]["desc"]
                    )
                    
                    model_ethnicity_dropdown = gr.Dropdown(
                        label="🌍 인종",
                        choices=[(ethnicity_opts[key]["name"], key) for key in ethnicity_opts.keys()],
                        value="none",
                        info=ethnicity_opts["none"]["desc"]
                    )
                    
                    model_hairstyle_dropdown = gr.Dropdown(
                        label="💇 헤어스타일",
                        choices=[(hair_opts[key]["name"], key) for key in hair_opts.keys()],
                        value="none",
                        info=hair_opts["none"]["desc"]
                    )
                    
                    model_hair_color_dropdown = gr.Dropdown(
                        label="🎨 머리색",
                        choices=[(hair_color_opts[key]["name"], key) for key in hair_color_opts.keys()],
                        value="none",
                        info=hair_color_opts["none"]["desc"]
                    )
                    
                    model_height_number = gr.Number(
                        label="📏 키 (cm)",
                        value=None,
                        minimum=0,
                        step=0.1,
                        precision=1,
                        info="모델의 키를 입력하세요 (선택사항)"
                    )
                    
                    model_weight_number = gr.Number(
                        label="⚖️ 몸무게 (kg)",
                        value=None,
                        minimum=0,
                        step=0.1,
                        precision=1,
                        info="모델의 몸무게를 입력하세요 (선택사항)"
                    )
                    
                with gr.Column(scale=1):
                    # "설정 안 함" 옵션 추가
                    main_category_choices = [(catalog[key]["name"], key) for key in catalog.keys()]
                    
                    model_main_category_dropdown = gr.Dropdown(
                        label="📂 메인 카테고리",
                        choices=main_category_choices,
                        value="none",
                        info="의류 메인 카테고리 선택"
                    )
                    
                    # 기본 서브 카테고리는 "설정 안 함"만 표시
                    model_sub_category_dropdown = gr.Dropdown(
                        label="📁 서브 카테고리",
                        choices=[("설정 안 함", "none")],
                        value="none",
                        info="메인 카테고리에 따라 변경됩니다"
                    )
                    
                    model_fit_dropdown = gr.Dropdown(
                        label="👔 핏",
                        choices=[(fit_opts[key]["name"], key) for key in fit_opts.keys()],
                        value="none",
                        info=fit_opts["none"]["desc"]
                    )
                    
                    model_sleeve_dropdown = gr.Dropdown(
                        label="👕 소매 길이",
                        choices=[(sleeve_opts[key]["name"], key) for key in sleeve_opts.keys()],
                        value="none",
                        info=sleeve_opts["none"]["desc"]
                    )
                    
                    model_length_dropdown = gr.Dropdown(
                        label="📏 기장",
                        choices=[(length_opts[key]["name"], key) for key in length_opts.keys()],
                        value="none",
                        info=length_opts["none"]["desc"]
                    )
                    
                    model_wear_together_textbox = gr.Textbox(
                        label="👔 함께 입을 옷",
                        value="",
                        placeholder="예: black pants, white sneakers",
                        info="함께 입을 다른 의류를 입력하세요 (선택사항)"
                    )
                    
                    model_total_length_number = gr.Number(
                        label="📏 전체 기장 (cm)",
                        value=None,
                        minimum=0,
                        step=0.1,
                        precision=1,
                        info="전체 기장을 입력하세요 (선택사항)"
                    )
                
                with gr.Column(scale=2):
                    # 초기 프롬프트 생성 (의상 옵션 없음)
                    initial_model_options = ModelOptions(gender="woman", age="young")
                    initial_prompt = assemble_model_prompt(
                        type="front",
                        model_options=initial_model_options,
                        clothes_options=None
                    )
                    
                    model_prompt_display = gr.Textbox(
                        label="📝 생성된 프롬프트",
                        value=initial_prompt,
                        lines=15,
                        interactive=False,
                        max_lines=20
                    )
            
            # 메인 카테고리 변경 시 서브 카테고리와 프롬프트 업데이트
            def update_model_sub_category_choices(main_category, view_type, gender, age, skin_tone, ethnicity, hairstyle, hair_color, height, weight, sleeve, length, fit, wear_together, total_length):
                """메인 카테고리에 따라 서브 카테고리 선택지를 업데이트하고 프롬프트도 업데이트"""
                # catalog의 children에 이미 "none" 옵션이 포함되어 있음
                if main_category in catalog:
                    sub_cats = catalog[main_category]["children"]
                    choices = [(sub_cats[key]["name"], key) for key in sub_cats.keys()]
                    sub_category_value = "none"
                    dropdown_update = gr.update(choices=choices, value="none")
                else:
                    # catalog에 없는 경우 기본값
                    sub_category_value = "none"
                    dropdown_update = gr.update(choices=[("설정 안 함", "none")], value="none")
                
                # 프롬프트도 함께 업데이트
                prompt = update_model_prompt(view_type, gender, age, skin_tone, ethnicity, hairstyle, hair_color, height, weight, main_category, sub_category_value, sleeve, length, fit, wear_together, total_length)
                return dropdown_update, prompt
            
            model_main_category_dropdown.change(
                fn=update_model_sub_category_choices,
                inputs=[
                    model_main_category_dropdown,
                    model_view_radio,
                    model_gender_radio,
                    model_age_dropdown,
                    model_skin_dropdown,
                    model_ethnicity_dropdown,
                    model_hairstyle_dropdown,
                    model_hair_color_dropdown,
                    model_height_number,
                    model_weight_number,
                    model_sleeve_dropdown,
                    model_length_dropdown,
                    model_fit_dropdown,
                    model_wear_together_textbox,
                    model_total_length_number
                ],
                outputs=[model_sub_category_dropdown, model_prompt_display]
            )
            
            # 모든 옵션 변경 시 프롬프트 업데이트
            model_option_inputs = [
                model_view_radio,
                model_gender_radio,
                model_age_dropdown,
                model_skin_dropdown,
                model_ethnicity_dropdown,
                model_hairstyle_dropdown,
                model_hair_color_dropdown,
                model_height_number,
                model_weight_number,
                model_main_category_dropdown,
                model_sub_category_dropdown,
                model_sleeve_dropdown,
                model_length_dropdown,
                model_fit_dropdown,
                model_wear_together_textbox,
                model_total_length_number
            ]
            
            # 메인 카테고리를 제외한 나머지 옵션들의 change 이벤트 등록
            for option_input in [
                model_view_radio,
                model_gender_radio,
                model_age_dropdown,
                model_skin_dropdown,
                model_ethnicity_dropdown,
                model_hairstyle_dropdown,
                model_hair_color_dropdown,
                model_height_number,
                model_weight_number,
                model_sub_category_dropdown,
                model_sleeve_dropdown,
                model_length_dropdown,
                model_fit_dropdown,
                model_wear_together_textbox,
                model_total_length_number
            ]:
                option_input.change(
                    fn=update_model_prompt,
                    inputs=model_option_inputs,
                    outputs=[model_prompt_display]
                )                   
    
    with gr.Tab("📸 상품 이미지 생성 프롬프트"):
        with gr.Column():
            gr.Markdown("## 상품 이미지 생성 프롬프트")
            gr.Markdown("평평한 상품 이미지를 생성하기 위한 프롬프트입니다.")
            
            with gr.Row():
                product_image_type_radio = gr.Radio(
                    label="🎯 이미지 타입",
                    choices=[
                        ("기본 (평평한 상품)", "default"), 
                        ("마네킹 제거", "mannequin"), 
                        ("사람 제거", "person")
                    ],
                    value="default",
                    info="상품 이미지 생성 방식 선택"
                )
            
            with gr.Row():
                product_image_prompt_display = gr.Textbox(
                    label="📝 Product Image 프롬프트",
                    value=product_image_prompt(type="default"),
                    lines=10,
                    interactive=False,
                    max_lines=15
                )
            
            # 타입 변경 시 프롬프트 업데이트
            def update_product_image_prompt(image_type):
                return product_image_prompt(type=image_type)
            
            product_image_type_radio.change(
                fn=update_product_image_prompt,
                inputs=[product_image_type_radio],
                outputs=[product_image_prompt_display]
            )
    
    with gr.Tab("↔️ 측면 이미지 생성 프롬프트"):
        with gr.Column():
            gr.Markdown("## 측면 이미지 생성 프롬프트")
            gr.Markdown("좌우 측면 이미지를 생성하기 위한 프롬프트입니다.")
            
            with gr.Row():
                side_view_gender_radio = gr.Radio(
                    label="👤 성별",
                    choices=[("여성", "woman"), ("남성", "man")],
                    value="woman",
                    info="모델 성별 선택"
                )
                
                side_view_direction_radio = gr.Radio(
                    label="↔️ 방향",
                    choices=[("왼쪽", "left"), ("오른쪽", "right"), ("뒤", "back")],
                    value="left",
                    info="측면 방향 선택"
                )
            
            with gr.Row():
                side_view_prompt_display = gr.Textbox(
                    label="📝 Side View 프롬프트",
                    value=side_view_prompt(side="left", gender="woman"),
                    lines=10,
                    interactive=False,
                    max_lines=15
                )
            
            # 성별 또는 방향 변경 시 프롬프트 업데이트
            def update_side_view_prompt(gender, direction):
                return side_view_prompt(side=direction, gender=gender)
            
            side_view_gender_radio.change(
                fn=update_side_view_prompt,
                inputs=[side_view_gender_radio, side_view_direction_radio],
                outputs=[side_view_prompt_display]
            )
            
            side_view_direction_radio.change(
                fn=update_side_view_prompt,
                inputs=[side_view_gender_radio, side_view_direction_radio],
                outputs=[side_view_prompt_display]
            )
        


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7862, share=True)

# PYTHONPATH=. uv run scripts/vto_gradio.py