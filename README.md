# Web Crawler & PDF Summarizer

A Python-based web crawler and PDF scraper that extracts and summarizes data from documents using LLMs. The project uses `Scrapy` to crawl URLs, downloads PDF files, processes them with a custom `PDFProcessor` built on top of `PyPDF2`, and sends the extracted content to a language model for summarization via prompt engineering.

---

## 🧠 Features

- Crawl and scrape PDF URLs from target websites
- Download and extract text from PDFs
- Parse only specific pages or the full document (customizable)
- Send extracted text to an LLM (OpenAI/Azure) for intelligent summarization
- Modular design with logging for better traceability

---

## 🛠 Tech Stack

- Python 3.x
- Scrapy — for web crawling
- PyPDF2 — to extract text from PDF files
- OpenAI/Azure SDK — for generating summaries from the content

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Pip
- OpenAI or Azure API Key (for LLM summarization)

## 🧩 Project Structure
![image](https://github.com/user-attachments/assets/b7a59ffa-8f45-4476-aed8-b314b0aa8497)

## Sample Output
![image](https://github.com/user-attachments/assets/9112a32d-b795-4593-b26e-fd74f2a7ee07)


## 🧑‍💻 Contributing
Feel free to open issues or submit pull requests for enhancements or bug fixes.

## 🙌 Acknowledgments
### - Scrapy
### - PyPDF2
### - OpenAI API
