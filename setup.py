from setuptools import setup, find_packages

setup(
    name="intelligence",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "streamlit",
        "python-dotenv",
        "yt-dlp",
        "deepgram-sdk",
        "openai",
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
    ],
    python_requires=">=3.8",
) 