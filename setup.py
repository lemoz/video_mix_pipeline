from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dicer-ugc",
    version="0.1.0",
    author="Your Name",
    description="UGC video variation pipeline",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "typer[all]>=0.9.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "pyyaml>=6.0.1",
        "google-generativeai>=0.3.0",
        "elevenlabs>=0.2.0",
        "httpx>=0.25.0",
        "opencv-python>=4.8.0",
        "ffmpeg-python>=0.2.0",
        "numpy>=1.24.0",
        "rich>=13.7.0",
        "python-dotenv>=1.0.0",
        "tenacity>=8.2.0",
    ],
    entry_points={
        "console_scripts": [
            "dicer-ugc=dicer_ugc.cli:app",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)