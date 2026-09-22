import os

from dotenv import load_dotenv
from tavily import TavilyClient


# Load environment variables from .env
load_dotenv()


class WebSearchTool:
    """
    Web search tool using Tavily.
    """

    def __init__(self, max_results=5):
        self.max_results = max_results

        self.api_key = os.getenv("TAVILY_API_KEY")

        if not self.api_key:
            raise ValueError(
                "TAVILY_API_KEY not found in .env file."
            )

        self.client = TavilyClient(
            api_key=self.api_key
        )

    def search(self, query: str) -> str:
        """
        Search the web using Tavily.

        Args:
            query: Search question or keywords.

        Returns:
            Formatted search results.
        """

        if not query or not query.strip():
            return "Please provide a search query."

        try:
            response = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=self.max_results
            )

            results = response.get(
                "results",
                []
            )

            if not results:
                return "No search results found."

            formatted_results = []

            for result in results:
                title = result.get(
                    "title",
                    "No title"
                )

                url = result.get(
                    "url",
                    "No URL"
                )

                content = result.get(
                    "content",
                    "No content"
                )

                formatted_results.append(
                    f"Title: {title}\n"
                    f"URL: {url}\n"
                    f"Content: {content}"
                )

            return "\n\n----------------------\n\n".join(
                formatted_results
            )

        except Exception as error:
            return (
                f"Web search error: {str(error)}"
            )

    def __call__(self, query: str) -> str:
        """
        Allows the tool to be called like a function.
        """

        return self.search(query)


if __name__ == "__main__":

    print("=" * 60)
    print("       AGENTFORGE - TAVILY WEB SEARCH")
    print("=" * 60)

    try:
        search_tool = WebSearchTool(
            max_results=5
        )

        question = input(
            "\nEnter your search query: "
        ).strip()

        print("\nSearching the web...\n")

        result = search_tool.search(
            question
        )

        print("=" * 60)
        print("SEARCH RESULTS")
        print("=" * 60)

        print(result)

    except Exception as error:
        print("\nSYSTEM ERROR:")
        print(error)