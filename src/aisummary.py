from google import genai

class Summarizer:

    def __init__(self, config):
        self.client = genai.Client(api_key=config.get_gemini_api_key())
        self.logger = config.get_logger()
        self.prompt = config.get_ai_summary_prompt()
        self.model = config.get_gemini_model()
        

    def summarize(self, link_to_article) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=self.prompt + link_to_article,
            )
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
<<<<<<< HEAD
=======
            print("List of models that support generateContent:\n")
            models = self.client.models.list()
            if models:
                for m in models: # type: ignore
                    if m.supported_actions:
                        for action in m.supported_actions:
                            if action == "generateContent":
                                print(m.name)
>>>>>>> 91129fdf554b642d451f5a5b3f525770ff0c9163
            return ""

        return response.text if response and response.text else ""
    
