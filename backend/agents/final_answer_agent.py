import os
import json
from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class FinalAnswerAgent:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")

        self.client = Groq(api_key=api_key)

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b"
        )

    def generate_final_answer(self, original_question, agent_results):

        results_text = json.dumps(
            agent_results,
            indent=2,
            ensure_ascii=False
        )

        prompt = f"""
You are the Final Answer Agent in a multi-agent AI system called AgentForge.

Your job is to combine the results produced by different specialized agents
and provide one clear, accurate and useful final answer to the user.

Original User Question:
{original_question}

Results from Specialized Agents:
{results_text}

Instructions:

1. Understand the original user question.
2. Review all agent results.
3. Combine relevant information.
4. Remove duplicate or unnecessary information.
5. Do not mention internal agent names unless it is useful.
6. Do not invent information that is not supported by the agent results.
7. If an agent failed, ignore the failed result if other results are sufficient.
8. Present the answer in a clear and readable format.
9. Use headings, bullet points, numbered steps, or code blocks when useful.
10. If the task contains code, preserve the useful code.
11. Answer the original question directly.
12. Do not say "According to the agents".
13. Do not describe the internal workflow.
14. Return only the final answer.

Final Answer:
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional final-answer synthesis agent. "
                        "Produce accurate, concise and well-structured answers."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        return response.choices[0].message.content.strip()


if __name__ == "__main__":

    agent = FinalAnswerAgent()

    test_results = [
        {
            "step": 1,
            "agent": "RESEARCH",
            "task": "Explain polymorphism in C++.",
            "result": (
                "Polymorphism allows the same interface to represent "
                "different implementations. In C++, runtime polymorphism "
                "is commonly achieved using virtual functions."
            )
        },
        {
            "step": 2,
            "agent": "CODING",
            "task": "Provide a simple C++ example.",
            "result": """
#include <iostream>
using namespace std;

class Animal {
public:
    virtual void sound() {
        cout << "Animal sound";
    }
};

class Dog : public Animal {
public:
    void sound() override {
        cout << "Dog barks";
    }
};
"""
        }
    ]

    answer = agent.generate_final_answer(
        "Explain polymorphism in C++ and give an example.",
        test_results
    )

    print("\n========================================")
    print("FINAL ANSWER AGENT")
    print("========================================")
    print(answer)