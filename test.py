import anthropic
import os
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from PyPDF2 import PdfReader
import re

# Add color constants at the top
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def fetch_arxiv_papers(max_results=25):
    """Fetch recent papers from arXiv astro-ph webpage"""
    url = 'https://arxiv.org/list/astro-ph/recent'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        papers = []
        entries = soup.find_all(['dt', 'dd'])
        
        current_paper = {}
        for i, entry in enumerate(entries):
            if len(papers) >= max_results:
                break
                
            if entry.name == 'dt':
                arxiv_id = entry.find('a', {'title': 'Abstract'})
                if arxiv_id:
                    current_paper = {
                        'arxiv_id': arxiv_id.text.strip(),
                        'link': f"https://arxiv.org/abs/{arxiv_id.text.strip()}"
                    }
            
            elif entry.name == 'dd' and current_paper:
                title = entry.find('div', {'class': 'list-title'})
                if title:
                    current_paper['title'] = title.text.replace('Title:', '').strip()
                
                authors = entry.find('div', {'class': 'list-authors'})
                if authors:
                    current_paper['authors'] = authors.text.replace('Authors:', '').strip()
                
                abstract = entry.find('p', {'class': 'mathjax'})
                if abstract:
                    current_paper['abstract'] = abstract.text.strip()
                
                papers.append(current_paper)
                current_paper = {}
        
        return papers
    except Exception as e:
        print(f"Error fetching arXiv papers: {e}")
        return None

def save_paper_list(papers, filename="list_of_papers.txt"):
    """Save the list of papers to a file"""
    if not papers:
        print("No papers to save")
        return
        
    print(f"\n{Colors.BLUE}{'='*80}")
    print("PAPERS RETRIEVED FROM ARXIV")
    print(f"{'='*80}{Colors.ENDC}\n")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"ArXiv Astrophysics Papers List (Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
        f.write("=" * 80 + "\n\n")
        
        for i, paper in enumerate(papers, 1):
            paper_info = f"{Colors.CYAN}{i}. {paper.get('title', 'No title')}\n"
            paper_info += f"   Authors: {paper.get('authors', 'No authors')}\n"
            paper_info += f"   arXiv ID: {paper.get('arxiv_id', 'No ID')}\n"
            paper_info += f"   Link: {paper.get('link', 'No link')}\n"
            paper_info += f"   Abstract: {paper.get('abstract', 'No abstract')}\n{Colors.ENDC}"
            
            print(paper_info)  # Print to console
            # Remove color codes for file writing
            f.write(paper_info.replace(Colors.CYAN, '').replace(Colors.ENDC, ''))
            f.write("-" * 80 + "\n\n")

def read_prompt():
    """Read the prompt from prompt.txt"""
    with open('prompt.txt', 'r') as f:
        return f.read()

def get_claude_to_select_paper(papers):
    """Have Claude select the most suitable paper for hypergraph analysis"""
    print(f"\n{Colors.YELLOW}{'='*80}")
    print("CLAUDE PAPER SELECTION PROCESS")
    print(f"{'='*80}{Colors.ENDC}")
    print(f"\n{Colors.CYAN}Asking Claude to select the most suitable paper for hypergraph analysis...{Colors.ENDC}\n")
    
    client = anthropic.Client()
    
    papers_text = "\n\n".join([
        f"Paper {i+1}:\nTitle: {paper.get('title', 'No title')}\nAbstract: {paper.get('abstract', 'No abstract available')}"
        for i, paper in enumerate(papers)
    ])
    
    selection_prompt = f"""Here are {len(papers)} recent astrophysics papers from arXiv. 
Please select the paper that would be most suitable for converting into hypergraph rules 
based on its physical concepts and mathematical structure. Consider papers that discuss 
fundamental physics, cosmology, or complex systems.

{papers_text}

Please respond with only the number of the selected paper and a brief explanation why.
Format: "Paper X - explanation" """

    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0.7,
            system="You are an expert in physics and hypergraphs.",
            messages=[{
                "role": "user",
                "content": selection_prompt
            }]
        )
        return message.content[0].text if message.content else None
    except Exception as e:
        print(f"Error calling Claude API for paper selection: {e}")
        return None

def get_paper_text(arxiv_id):
    """Get paper text from arXiv API"""
    url = f"https://export.arxiv.org/pdf/{arxiv_id}"
    try:
        print(f"{Colors.CYAN}Downloading paper PDF from {url}...{Colors.ENDC}")
        response = requests.get(url)
        response.raise_for_status()
        
        # Save PDF temporarily
        with open('temp_paper.pdf', 'wb') as f:
            f.write(response.content)
            
        print("Extracting text from PDF...")
        # Extract text
        with open('temp_paper.pdf', 'rb') as f:
            reader = PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
                
        # Clean up
        os.remove('temp_paper.pdf')
        return text
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return None
    except Exception as e:
        print(f"Error processing PDF: {e}")
        if os.path.exists('temp_paper.pdf'):
            os.remove('temp_paper.pdf')  # Clean up if file exists
        return None

def get_claude_analysis(prompt, paper_text, paper_info):
    """Get Claude's hypergraph analysis of the paper"""
    print(f"\n{Colors.GREEN}{'='*80}")
    print("HYPERGRAPH ANALYSIS PROCESS")
    print(f"{'='*80}{Colors.ENDC}")
    print(f"\n{Colors.CYAN}Asking Claude to analyze the paper and generate hypergraph rules...{Colors.ENDC}\n")
    
    client = anthropic.Client()
    
    full_prompt = f"""Here is the paper information:
Title: {paper_info.get('title', 'No title')}
Authors: {paper_info.get('authors', 'No authors')}
Abstract: {paper_info.get('abstract', 'No abstract available')}

Full paper text:
{paper_text}

Based on this paper and following these instructions:

{prompt}

Please generate appropriate hypergraph rules."""
    
    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            temperature=0.7,
            system="You are an expert in physics and hypergraphs. Analyze the given paper and create Wolfram-style hypergraph rules.",
            messages=[{
                "role": "user",
                "content": full_prompt
            }]
        )
        return message.content[0].text if message.content else None
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return None

def save_response(response, filename="claude_response.txt"):
    """Save Claude's response to a file"""
    if response is None:
        print("No response to save")
        return
        
    with open(filename, 'w') as f:
        f.write(response)

def save_wolfram_code(response, filename="wolfram_rules.txt"):
    """Extract and save Wolfram code sections from Claude's response"""
    if response is None:
        print(f"{Colors.RED}No response to extract Wolfram code from{Colors.ENDC}")
        return
        
    # Find all code blocks between ``` markers
    wolfram_blocks = re.findall(r'```(?:wolfram)?(.*?)```', response, re.DOTALL)
    
    if not wolfram_blocks:
        print(f"{Colors.YELLOW}No Wolfram code blocks found in the response{Colors.ENDC}")
        return
        
    print(f"\n{Colors.GREEN}Saving Wolfram code to {filename}...{Colors.ENDC}")
    
    with open(filename, 'w') as f:
        f.write("(* Generated Wolfram Rules from ArXiv Paper Analysis *)\n\n")
        for i, block in enumerate(wolfram_blocks, 1):
            f.write(f"(* Block {i} *)\n")
            f.write(block.strip() + "\n\n")
            
    print(f"{Colors.GREEN}Wolfram code saved successfully!{Colors.ENDC}")

def main():
    # Fetch papers
    papers = fetch_arxiv_papers()
    if not papers:
        print("Failed to fetch papers from arXiv")
        return
    
    # Save and display paper list
    save_paper_list(papers)
    
    # Have Claude select a paper
    selection = get_claude_to_select_paper(papers)
    if not selection:
        print("Failed to get paper selection from Claude")
        return
    
    print(f"\n{Colors.YELLOW}CLAUDE'S SELECTION AND REASONING:")
    print("-"*40)
    print(f"{Colors.CYAN}{selection}{Colors.ENDC}")
    print(f"{Colors.YELLOW}{'-'*40}{Colors.ENDC}")
    
    # Extract paper number from Claude's response
    try:
        paper_num = int(selection.split()[1]) - 1
        selected_paper = papers[paper_num]
        print(f"\n{Colors.YELLOW}SELECTED PAPER DETAILS:")
        print("-"*40)
        print(f"{Colors.CYAN}Title: {selected_paper['title']}")
        print(f"Authors: {selected_paper['authors']}")
        print(f"arXiv ID: {selected_paper['arxiv_id']}{Colors.ENDC}")
        print(f"{Colors.YELLOW}{'-'*40}{Colors.ENDC}")
    except Exception as e:
        print(f"Error parsing paper selection: {e}")
        return
    
    # Get paper text
    print(f"\n{Colors.CYAN}Downloading and processing paper...{Colors.ENDC}")
    paper_text = get_paper_text(selected_paper['arxiv_id'])
    if not paper_text:
        print("Failed to get paper text")
        return
    
    # Get prompt and analyze paper
    prompt = read_prompt()
    response = get_claude_analysis(prompt, paper_text, selected_paper)
    
    if response:
        print(f"\n{Colors.GREEN}HYPERGRAPH ANALYSIS RESULTS:")
        print("="*80)
        print(f"{Colors.CYAN}{response}{Colors.ENDC}")
        print(f"{Colors.GREEN}{'='*80}{Colors.ENDC}")
        
        save_response(response)
        print(f"\n{Colors.GREEN}Analysis saved to claude_response.txt{Colors.ENDC}")
        
        # Add this line to save Wolfram code
        save_wolfram_code(response)
    else:
        print(f"{Colors.RED}Failed to get analysis from Claude{Colors.ENDC}")

if __name__ == "__main__":
    main()

