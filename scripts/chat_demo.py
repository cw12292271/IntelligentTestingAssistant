"""命令行对话入口。"""
from src.chain import conversation, structured_llm

def main():
    session_id = "cli_session_001"
    print("智能测试助手 v2（输入 exit 退出）")
    print("-" * 40)

    while True:
        user_input = input("\n你: ")
        if user_input.lower() in ["exit", "quit", "退出"]:
            print("助手: 再见！")
            break

        # 普通对话（带记忆）
        resp = conversation.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}},
        )
        print(f"助手: {resp.content}")

        # 如果用户说“生成用例”，走结构化输出
        if "生成用例" in user_input or "测试用例" in user_input:
            case = structured_llm.invoke(user_input)
            print("\n[结构化用例]")
            print(f"  标题: {case.title}")
            print(f"  前置: {case.precondition}")
            print(f"  步骤: {case.steps}")
            print(f"  预期: {case.expected}")
            print(f"  类型: {case.case_type}")

if __name__ == "__main__":
    main()