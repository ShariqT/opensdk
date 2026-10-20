from opensdkv2.provider import WavespeedProvider

def test_model_provider():
    provider = WavespeedProvider("deepseek/glm", "myapiKey1")
    assert str(provider.base_url) == "https://llm.wavespeed.ai/v1"

