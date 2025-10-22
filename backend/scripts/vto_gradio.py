import gradio as gr
import io
from PIL import Image
from core.vto_service.gemini_handler import GeminiProcesser
from prompts.vto_model_prompts import assemble_model_prompt
from prompts.vto_prompts import assemble_prompt
from prompts.prod_image_prompts import product_image_prompt
from prompts.side_view_prompts import side_view_prompt
from core.litellm_hander.utils import gender_options, fit_options, sleeve_options, length_options, clothes_category

async def process_inputs(text_input, image1, image2, image3, temperature, num_images):
    """
    텍스트 입력과 이미지 입력들을 처리하는 함수
    """
    gemini_processer = GeminiProcesser(verbose=True)
    contents_list = []
    
    # 콘텐츠 생성 (이미지를 미리 변환)
    content_parts = [text_input]
    if image1 is not None:
        content_parts.append(await gemini_processer.create_image_content(image1))
    if image2 is not None:
        content_parts.append(await gemini_processer.create_image_content(image2))
    if image3 is not None:
        content_parts.append(await gemini_processer.create_image_content(image3))
    
    # 생성할 이미지 개수만큼 같은 content를 복사하여 추가
    for _ in range(num_images):
        contents_list.append(content_parts.copy())
    
    # VTO 추론 실행
    result = await gemini_processer.execute_vto_inference(
        contents_list=contents_list,
        front_has_images=True,  # 항상 True로 설정하여 생성된 이미지를 front_images에 담음
        back_has_images=False,
        image_count=num_images,
        temperature=temperature,
        include_side=False
    )
    
    # front_images를 bytes 리스트로 가져오기
    front_images = result.get("front_images", [])
    
    # bytes 데이터를 PIL Image로 변환
    pil_images = []
    for img_bytes in front_images:
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
                temperature = gr.Slider(
                    minimum=0.0,
                    maximum=2.0,
                    value=1.0,
                    step=0.1,
                    label="Temperature",
                    info="생성 모델의 창의성 조절 (낮을수록 일관적, 높을수록 다양함)"
                )
                
                num_images = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=3,
                    step=1,
                    label="생성할 이미지 개수",
                    info="생성할 이미지의 개수를 선택하세요"
                )
                submit_btn = gr.Button("🚀 실행", variant="primary")
        with gr.Row():
            image1 = gr.Image(
                label="이미지 1",
                type="pil",
                format="png",
                image_mode="RGB"
            )
            
            image2 = gr.Image(
                label="이미지 2 (선택사항)",
                type="pil",
                format="png",
                image_mode="RGB"
            )
            
            image3 = gr.Image(
                label="이미지 3 (선택사항)",
                type="pil",
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
                height=600,
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
            inputs=[text_input, image1, image2, image3, temperature, num_images],
            outputs=[output, usage_output, debug_output]
        )
    
    with gr.Tab("👔 가상 입어보기 프롬프트"):
        with gr.Column():
            gr.Markdown("## 모델에게 입히는 프롬프트")
            gr.Markdown("### 옵션 선택")
            
            # 옵션 데이터 준비
            gender_opts = gender_options()
            fit_opts = fit_options()
            sleeve_opts = sleeve_options()
            length_opts = length_options()
            catalog = clothes_category()
            
            with gr.Row():
                default_prompt_display = gr.Textbox(
                    label="📝 생성된 프롬프트",
                    value=assemble_prompt(
                        main_category="default",
                        sub_category="default",
                        replacement="clothing",
                    ),
                    lines=10,
                    interactive=False,
                    max_lines=15
                )
                with gr.Column():
                    # 성별 선택
                    gender_dropdown = gr.Dropdown(
                        label="👤 성별",
                        choices=[("선택 안 함", "none")] + [(gender_opts[key]["name"], key) for key in gender_opts.keys()],
                        value="none",
                        info=gender_opts["person"]["desc"]
                    )
                    
                    # 메인 카테고리 선택
                    main_category_dropdown = gr.Dropdown(
                        label="📂 메인 카테고리",
                        choices=[("Default", "default")] + [(catalog[key]["name"], key) for key in catalog.keys()],
                        value="default",
                        info="의류 메인 카테고리 선택"
                    )
                    
                    # 서브 카테고리 선택
                    sub_category_dropdown = gr.Dropdown(
                        label="📁 서브 카테고리",
                        choices=["default"],
                        value="default",
                        info="메인 카테고리에 따라 변경됩니다"
                    )
                    
                    # Replacement 입력
                    replacement_input = gr.Textbox(
                        label="🔄 Replacement",
                        value="clothing",
                        info="대체할 의상 부위 (예: clothing, tops, bottoms)"
                    )
                
                with gr.Column():
                    # 핏 선택
                    fit_dropdown = gr.Dropdown(
                        label="👔 핏",
                        choices=[(fit_opts[key]["name"], key) for key in fit_opts.keys()],
                        value="none",
                        info=fit_opts["none"]["desc"]
                    )
                    
                    # 소매 길이 선택
                    sleeve_dropdown = gr.Dropdown(
                        label="👕 소매 길이",
                        choices=[(sleeve_opts[key]["name"], key) for key in sleeve_opts.keys()],
                        value="none",
                        info=sleeve_opts["none"]["desc"]
                    )
                    
                    # 기장 선택
                    length_dropdown = gr.Dropdown(
                        label="📏 기장",
                        choices=[(length_opts[key]["name"], key) for key in length_opts.keys()],
                        value="none",
                        info=length_opts["none"]["desc"]
                    )
            
            # 메인 카테고리 변경 시 서브 카테고리와 프롬프트 업데이트
            main_category_dropdown.change(
                fn=update_sub_category_choices,
                inputs=[
                    main_category_dropdown,
                    replacement_input,
                    gender_dropdown,
                    fit_dropdown,
                    sleeve_dropdown,
                    length_dropdown
                ],
                outputs=[sub_category_dropdown, default_prompt_display]
            )
            
            # 나머지 옵션 변경 시 프롬프트만 업데이트 (메인 카테고리 제외)
            other_option_inputs = [
                main_category_dropdown,
                sub_category_dropdown,
                replacement_input,
                gender_dropdown,
                fit_dropdown,
                sleeve_dropdown,
                length_dropdown
            ]
            
            # 메인 카테고리를 제외한 나머지 옵션들의 change 이벤트 등록
            for option_input in [sub_category_dropdown, replacement_input, gender_dropdown, fit_dropdown, sleeve_dropdown, length_dropdown]:
                option_input.change(
                    fn=update_prompt,
                    inputs=other_option_inputs,
                    outputs=[default_prompt_display]
                )
    
    with gr.Tab("🧑 가상 모델 생성 프롬프트"):
        with gr.Column():
            gr.Markdown("## 가상 모델 생성 프롬프트")
            gr.Markdown("Front View와 Back View 모델 이미지를 생성하기 위한 프롬프트입니다.")
            with gr.Row():
                front_prompt_display = gr.Textbox(
                    label="📝 Front View 프롬프트",
                    value=assemble_model_prompt(type="front"),
                    lines=15,
                    interactive=False,
                    max_lines=15
                )
                back_prompt_display = gr.Textbox(
                    label="📝 Back View 프롬프트",
                    value=assemble_model_prompt(type="back"),
                    lines=15,
                    interactive=False,
                    max_lines=15
                )
    
    with gr.Tab("📸 상품 이미지 생성 프롬프트"):
        with gr.Column():
            gr.Markdown("## 상품 이미지 생성 프롬프트")
            gr.Markdown("평평한 상품 이미지를 생성하기 위한 프롬프트입니다.")
            with gr.Row():
                product_image_prompt_display = gr.Textbox(
                    label="📝 Product Image 프롬프트",
                    value=product_image_prompt(type="default"),
                    lines=10,
                    interactive=False,
                    max_lines=15
                )
    
    with gr.Tab("↔️ 측면 이미지 생성 프롬프트"):
        with gr.Column():
            gr.Markdown("## 측면 이미지 생성 프롬프트")
            gr.Markdown("좌우 측면 이미지를 생성하기 위한 프롬프트입니다.")
            with gr.Row():
                with gr.Column():
                    side_view_left_prompt_display = gr.Textbox(
                        label="📝 Left Side View 프롬프트",
                        value=side_view_prompt(side="left"),
                        lines=10,
                        interactive=False,
                        max_lines=15
                    )
                with gr.Column():
                    side_view_right_prompt_display = gr.Textbox(
                        label="📝 Right Side View 프롬프트",
                        value=side_view_prompt(side="right"),
                        lines=10,
                        interactive=False,
                        max_lines=15
                    )
        


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7862, share=True)

# PYTHONPATH=. uv run scripts/vto_gradio.py