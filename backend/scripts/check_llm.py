"""检查客服 LLM 配置与连通性。

    .venv/Scripts/python.exe -m scripts.check_llm

不配 Key 时只打印当前模式；配了 Key 会真发一条请求，验证 base_url / model / Key 是否可用。
"""

from langchain_core.messages import HumanMessage

from app.support.llm import SupportLLM


def main() -> int:
    llm = SupportLLM()
    print(f"base_url : {llm.base_url}")
    print(f"model    : {llm.model}")
    print(f"api_key  : {'已配置（%d 字符）' % len(llm.api_key) if llm.api_key else '未配置'}")

    if not llm.enabled:
        print("\n当前走内置规则引擎（mode=rule），不会出网。")
        print("要接真模型：在 backend/.env 填 SUPPORT_LLM_API_KEY 后重启后端。")
        return 0

    state = {
        "messages": [HumanMessage(content="这个有货吗")],
        "intent": "chitchat",
        "nickname": "测试",
        "user_id": None,
        "policy_hits": [],
        "tool_result": None,
    }
    result = llm.reply(state)
    print(f"\n调用结果 : {result.source}")
    print(f"回复内容 : {result.text[:300]}")
    if result.source == "fallback":
        print("\n调用失败已回退规则引擎，请检查 base_url / model / 余额 / 网络。")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
