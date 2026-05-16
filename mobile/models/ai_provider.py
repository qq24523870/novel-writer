import json
import threading
from typing import Any, Callable, Dict, Generator, List, Optional
from utils.logger import logger
from utils.config_manager import config_manager


class AIProvider:
    """AI模型提供者基类"""

    def __init__(self, config: Dict):
        self.config = config
        self._initialized = False

    def initialize(self) -> bool:
        """初始化模型"""
        raise NotImplementedError

    def generate(self, prompt: str, system_prompt: str = "",
                 max_tokens: int = 2048, temperature: float = 0.8,
                 callback: Callable[[str], None] = None) -> str:
        """生成文本

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            max_tokens: 最大生成token数
            temperature: 温度参数
            callback: 流式回调函数

        Returns:
            生成的文本
        """
        raise NotImplementedError

    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self._initialized


class OpenAIProvider(AIProvider):
    """OpenAI API提供者"""

    def initialize(self) -> bool:
        try:
            import openai
            api_key = self.config.get("api_key", "")
            api_base = self.config.get("api_base", "https://api.openai.com/v1")
            if not api_key:
                logger.warning("OpenAI API密钥未配置")
                return False
            self.client = openai.OpenAI(api_key=api_key, base_url=api_base)
            self.model = self.config.get("model", "gpt-3.5-turbo")
            self._initialized = True
            logger.info(f"OpenAI模型初始化成功: {self.model}")
            return True
        except ImportError:
            logger.warning("openai库未安装")
            return False
        except Exception as e:
            logger.error(f"OpenAI初始化失败: {e}")
            return False

    def generate(self, prompt: str, system_prompt: str = "",
                 max_tokens: int = 2048, temperature: float = 0.8,
                 callback: Callable[[str], None] = None) -> str:
        if not self._initialized:
            return ""

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            if callback:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True
                )
                full_text = ""
                for chunk in response:
                    if not chunk.choices:
                        continue
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_text += content
                        callback(content)
                return full_text
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI生成失败: {e}")
            return f"生成失败: {str(e)}"


class WenxinProvider(AIProvider):
    """百度文心一言API提供者"""

    def initialize(self) -> bool:
        try:
            import requests
            self.api_key = self.config.get("api_key", "")
            self.secret_key = self.config.get("secret_key", "")
            self.model = self.config.get("model", "ernie-3.5-8k")
            if not self.api_key or not self.secret_key:
                logger.warning("文心一言API密钥未配置")
                return False
            self._get_access_token()
            self._initialized = True
            logger.info("文心一言模型初始化成功")
            return True
        except Exception as e:
            logger.error(f"文心一言初始化失败: {e}")
            return False

    def _get_access_token(self):
        """获取文心一言access_token"""
        import requests
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        response = requests.post(url, params=params)
        self.access_token = response.json().get("access_token", "")

    def generate(self, prompt: str, system_prompt: str = "",
                 max_tokens: int = 2048, temperature: float = 0.8,
                 callback: Callable[[str], None] = None) -> str:
        import requests
        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{self.model}?access_token={self.access_token}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "stream": callback is not None
        }

        try:
            if callback:
                response = requests.post(url, json=payload, stream=True)
                full_text = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode().replace("data: ", ""))
                            if "result" in data:
                                full_text += data["result"]
                                callback(data["result"])
                        except:
                            pass
                return full_text
            else:
                response = requests.post(url, json=payload)
                result = response.json()
                return result.get("result", "")
        except Exception as e:
            logger.error(f"文心一言生成失败: {e}")
            return f"生成失败: {str(e)}"


class TongyiProvider(AIProvider):
    """阿里通义千问API提供者"""

    def initialize(self) -> bool:
        try:
            from dashscope import Generation
            api_key = self.config.get("api_key", "")
            if not api_key:
                logger.warning("通义千问API密钥未配置")
                return False
            import dashscope
            dashscope.api_key = api_key
            self.model = self.config.get("model", "qwen-turbo")
            self._initialized = True
            logger.info("通义千问模型初始化成功")
            return True
        except ImportError:
            logger.warning("dashscope库未安装")
            return False
        except Exception as e:
            logger.error(f"通义千问初始化失败: {e}")
            return False

    def generate(self, prompt: str, system_prompt: str = "",
                 max_tokens: int = 2048, temperature: float = 0.8,
                 callback: Callable[[str], None] = None) -> str:
        from dashscope import Generation
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            responses = Generation.call(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=callback is not None,
                result_format="message"
            )

            if callback:
                full_text = ""
                for response in responses:
                    if response.output.choices[0].message.content:
                        content = response.output.choices[0].message.content
                        full_text += content
                        callback(content)
                return full_text
            else:
                return responses.output.choices[0].message.content
        except Exception as e:
            logger.error(f"通义千问生成失败: {e}")
            return f"生成失败: {str(e)}"


class LocalModelProvider(AIProvider):
    """本地大模型提供者（llama-cpp-python）"""

    def initialize(self) -> bool:
        try:
            from llama_cpp import Llama
            model_path = self.config.get("model_path", "")
            if not model_path:
                logger.warning("本地模型路径未配置")
                return False

            self.llm = Llama(
                model_path=model_path,
                n_ctx=self.config.get("n_ctx", 4096),
                n_gpu_layers=self.config.get("n_gpu_layers", 0),
                n_threads=self.config.get("n_threads", 4),
                verbose=self.config.get("verbose", False)
            )
            self._initialized = True
            logger.info(f"本地模型加载成功: {model_path}")
            return True
        except ImportError:
            logger.warning("llama-cpp-python库未安装")
            return False
        except Exception as e:
            logger.error(f"本地模型加载失败: {e}")
            return False

    def generate(self, prompt: str, system_prompt: str = "",
                 max_tokens: int = 2048, temperature: float = 0.8,
                 callback: Callable[[str], None] = None) -> str:
        if not self._initialized:
            return ""

        full_prompt = system_prompt + "\n\n" + prompt if system_prompt else prompt

        try:
            if callback:
                output = self.llm(
                    full_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True
                )
                full_text = ""
                for chunk in output:
                    if "choices" in chunk and chunk["choices"]:
                        content = chunk["choices"][0].get("text", "")
                        if content:
                            full_text += content
                            callback(content)
                return full_text
            else:
                output = self.llm(
                    full_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return output["choices"][0]["text"]
        except Exception as e:
            logger.error(f"本地模型生成失败: {e}")
            return f"生成失败: {str(e)}"


class OpenAICompatibleProvider(AIProvider):
    """OpenAI兼容接口基类（适用于所有使用OpenAI API格式的服务）"""

    def __init__(self, config: Dict, default_base_url: str = "", default_model: str = ""):
        super().__init__(config)
        self._default_base_url = default_base_url
        self._default_model = default_model

    def initialize(self) -> bool:
        try:
            import openai
            api_key = self.config.get("api_key", "")
            api_base = self.config.get("api_base", self._default_base_url)
            if not api_key:
                logger.warning(f"[{self.__class__.__name__}] API密钥未配置")
                return False
            if not api_base:
                logger.warning(f"[{self.__class__.__name__}] API地址未配置")
                return False
            self.client = openai.OpenAI(api_key=api_key, base_url=api_base)
            self.model = self.config.get("model", self._default_model)
            self._initialized = True
            logger.info(f"[{self.__class__.__name__}] 初始化成功: {self.model} @ {api_base}")
            return True
        except ImportError:
            logger.warning("openai库未安装")
            return False
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] 初始化失败: {e}")
            return False

    def generate(self, prompt: str, system_prompt: str = "",
                 max_tokens: int = 2048, temperature: float = 0.8,
                 callback: Callable[[str], None] = None) -> str:
        if not self._initialized:
            return ""

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            if callback:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True
                )
                full_text = ""
                for chunk in response:
                    if not chunk.choices:
                        continue
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_text += content
                        callback(content)
                return full_text
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] 生成失败: {e}")
            return f"生成失败: {str(e)}"


class CustomProvider(OpenAICompatibleProvider):
    """自定义大模型接口 - 用户可自由配置API地址、密钥和模型名称"""

    def __init__(self, config: Dict):
        super().__init__(config, default_base_url="", default_model="")


class SiliconFlowProvider(OpenAICompatibleProvider):
    """硅基流动 (SiliconFlow) API - https://siliconflow.cn"""

    SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
    SILICONFLOW_MODELS = [
        "deepseek-ai/DeepSeek-V3.2",
        "deepseek-ai/DeepSeek-V3",
        "deepseek-ai/DeepSeek-R1",
        "Qwen/Qwen2.5-72B-Instruct",
        "Qwen/Qwen2.5-32B-Instruct",
        "Qwen/Qwen2.5-14B-Instruct",
        "Qwen/Qwen2.5-7B-Instruct",
        "THUDM/glm-4-9b-chat",
        "internlm/internlm2_5-20b-chat",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "meta-llama/Meta-Llama-3.1-8B-Instruct",
    ]

    def __init__(self, config: Dict):
        config["api_base"] = self.SILICONFLOW_BASE_URL
        if not config.get("model"):
            config["model"] = self.SILICONFLOW_MODELS[0]
        super().__init__(config, default_base_url=self.SILICONFLOW_BASE_URL,
                         default_model=self.SILICONFLOW_MODELS[0])


class DeepSeekProvider(OpenAICompatibleProvider):
    """深度求索 (DeepSeek) API - https://deepseek.com"""

    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEEPSEEK_MODELS = [
        "deepseek-chat",
        "deepseek-reasoner",
    ]

    def __init__(self, config: Dict):
        config["api_base"] = self.DEEPSEEK_BASE_URL
        if not config.get("model"):
            config["model"] = self.DEEPSEEK_MODELS[0]
        super().__init__(config, default_base_url=self.DEEPSEEK_BASE_URL,
                         default_model=self.DEEPSEEK_MODELS[0])


class AIManager:
    """AI模型管理器，管理所有AI提供者"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = False
            self._providers: Dict[str, AIProvider] = {}
            self._current_provider: Optional[str] = None
            self._lock = threading.Lock()

    def initialize(self):
        """初始化所有配置的AI提供者"""
        self._providers: Dict[str, AIProvider] = {}
        self._current_provider: Optional[str] = None
        ai_config = config_manager.get("ai", {})
        cloud_config = ai_config.get("cloud_models", {})
        local_config = ai_config.get("local_model", {})

        provider_map = {
            "openai": (OpenAIProvider, cloud_config.get("openai", {})),
            "wenxin": (WenxinProvider, cloud_config.get("wenxin", {})),
            "tongyi": (TongyiProvider, cloud_config.get("tongyi", {})),
            "custom": (CustomProvider, cloud_config.get("custom", {})),
            "siliconflow": (SiliconFlowProvider, cloud_config.get("siliconflow", {})),
            "deepseek": (DeepSeekProvider, cloud_config.get("deepseek", {})),
        }

        for name, (provider_class, cfg) in provider_map.items():
            if cfg.get("enabled", False) and cfg.get("api_key", ""):
                provider = provider_class(cfg)
                if provider.initialize():
                    self._providers[name] = provider

        if local_config.get("enabled", False) and local_config.get("model_path", ""):
            local_provider = LocalModelProvider(local_config)
            if local_provider.initialize():
                self._providers["local"] = local_provider

        default = ai_config.get("default_model", "openai")
        if default in self._providers:
            self._current_provider = default
        elif self._providers:
            self._current_provider = list(self._providers.keys())[0]

        self._initialized = True
        logger.info(f"AI管理器初始化完成，可用模型: {list(self._providers.keys())}")

    def get_provider(self, name: str = "") -> Optional[AIProvider]:
        if not name:
            name = self._current_provider or ""
        return self._providers.get(name)

    def set_current_provider(self, name: str):
        if name in self._providers:
            self._current_provider = name
            config_manager.set("ai.default_model", name)
            logger.info(f"切换AI模型为: {name}")

    def get_available_providers(self) -> List[str]:
        return list(self._providers.keys())

    def generate(self, prompt: str, system_prompt: str = "",
                 max_tokens: int = 2048, temperature: float = 0.8,
                 provider: str = "",
                 callback: Callable[[str], None] = None) -> str:
        provider_instance = self.get_provider(provider)
        if not provider_instance:
            return "错误: 没有可用的AI模型，请先在设置中配置API密钥或本地模型路径"
        return provider_instance.generate(
            prompt=prompt, system_prompt=system_prompt,
            max_tokens=max_tokens, temperature=temperature, callback=callback
        )

    def generate_async(self, prompt: str, system_prompt: str = "",
                       max_tokens: int = 2048, temperature: float = 0.8,
                       provider: str = "",
                       on_complete: Callable[[str], None] = None,
                       on_error: Callable[[str], None] = None,
                       on_token: Callable[[str], None] = None):
        def _run():
            try:
                result = self.generate(
                    prompt=prompt, system_prompt=system_prompt,
                    max_tokens=max_tokens, temperature=temperature,
                    provider=provider, callback=on_token
                )
                if on_complete:
                    on_complete(result)
            except Exception as e:
                logger.error(f"异步AI生成失败: {e}")
                if on_error:
                    on_error(str(e))
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()


ai_manager = AIManager()