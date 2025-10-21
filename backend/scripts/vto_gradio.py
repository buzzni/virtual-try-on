import gradio as gr
import io
from PIL import Image
from core.vto_service.gemini_handler import GeminiProcesser
from prompts.vto_model_prompts import assemble_model_prompt
from prompts.vto_prompts import assemble_prompt
from prompts.prod_image_prompts import product_image_prompt
from prompts.side_view_prompts import side_view_prompt

async def process_inputs(text_input, image1, image2, image3, temperature, num_images):
    """
    텍스트 입력과 이미지 입력들을 처리하는 함수
    """
    gemini_processer = GeminiProcesser(verbose=True)
    contents_list = []
    
    # 콘텐츠 생성
    content = [text_input]
    if image1 is not None:
        content.append(await gemini_processer.create_image_content(image1))
    if image2 is not None:
        content.append(await gemini_processer.create_image_content(image2))
    if image3 is not None:
        content.append(await gemini_processer.create_image_content(image3))
    
    # 생성할 이미지 개수만큼 contents_list에 추가
    for _ in range(num_images):
        contents_list.append(content)
    
    # VTO 추론 실행
    result = await gemini_processer.execute_vto_inference(
        contents_list=contents_list,
        front_has_images=image1 is not None,
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
                submit_btn = gr.Button("처리하기", variant="primary")
                
            with gr.Column():
                temperature = gr.Slider(
                    minimum=0.0,
                    maximum=2.0,
                    value=0.7,
                    step=0.1,
                    label="Temperature",
                    info="생성 모델의 창의성 조절 (낮을수록 일관적, 높을수록 다양함)"
                )
                
                num_images = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=1,
                    step=1,
                    label="생성할 이미지 개수",
                    info="생성할 이미지의 개수를 선택하세요"
                )
        with gr.Row():
            image1 = gr.Image(
                label="이미지 1",
                type="pil"
            )
            
            image2 = gr.Image(
                label="이미지 2 (선택사항)",
                type="pil"
            )
            
            image3 = gr.Image(
                label="이미지 3 (선택사항)",
                type="pil"
            )
            
        with gr.Row():
            output = gr.Gallery(
                label="VTO 결과",
                show_label=False,
                elem_id="output_gallery",
                columns=3,
                rows=3,
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
    
    with gr.Tab("💡 참고용 프롬프트 예제"):
        with gr.Column():
            gr.Markdown("## 모델에게 입히는 프롬프트")
            with gr.Row():
                default_prompt_display = gr.Textbox(
                    label="📝 Default 프롬프트",
                    value=assemble_prompt(
                        main_category="default",
                        sub_category="default",
                        replacement="clothing",
                    ),
                    lines=7,
                    interactive=False,
                    max_lines=7
                )
            gr.Markdown("## 가상 모델 생성 프롬프트")
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
            gr.Markdown("## 상품 이미지 생성 프롬프트")
            with gr.Row():
                product_image_prompt_display = gr.Textbox(
                    label="📝 Product Image 프롬프트",
                    value=product_image_prompt(type="default"),
                    lines=7,
                    interactive=False,
                    max_lines=7
                )
            gr.Markdown("## 측면 이미지 생성 프롬프트")
            with gr.Row():
                side_view_prompt_display = gr.Textbox(
                    label="📝 Side View 프롬프트",
                    value=side_view_prompt(side="left"),
                    lines=7,
                    interactive=False,
                    max_lines=7
                )
        


if __name__ == "__main__":
    demo.launch(share=False)

# PYTHONPATH=. uv run scripts/vto_gradio.py