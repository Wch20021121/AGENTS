from chatbot import AIChatbot

def main():
    bot = AIChatbot()
    print("=== AI 对话助手 ===")
    print(f"{bot.get_model_info()}\n")
    print("命令: history/clear/models/models <编号>/addmodel <id> <name> <desc>/delmodel <编号>/exit\n")
    
    while True:
        try:
            user_input = input("你: ").strip()
            
            if user_input == "exit":
                print("再见！")
                break
            elif user_input == "history":
                print(bot.get_history())
            elif user_input == "clear":
                print(bot.clear())
            elif user_input == "models":
                print(bot.list_models())
            elif user_input.startswith("models "):
                try:
                    index = int(user_input[7:].strip())
                    print(bot.set_model(index))
                except ValueError:
                    print("请输入有效的数字编号")
            elif user_input.startswith("addmodel "):
                parts = user_input[9:].strip().split(maxsplit=2)
                if len(parts) >= 2:
                    model_id = parts[0]
                    name = parts[1]
                    desc = parts[2] if len(parts) > 2 else ""
                    print(bot.add_model(model_id, name, desc))
                else:
                    print("用法: addmodel <模型ID> <名称> [描述]")
            elif user_input.startswith("delmodel "):
                try:
                    index = int(user_input[9:].strip())
                    print(bot.remove_model(index))
                except ValueError:
                    print("请输入有效的数字编号")
            else:
                print(f"AI: {bot.chat(user_input)}\n")
        except KeyboardInterrupt:
            print("\n再见！")
            break

if __name__ == "__main__":
    main()
