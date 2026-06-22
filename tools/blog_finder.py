from ddgs.ddgs import DDGS


def search_blogs_ddg(keywords, max_results=15):
    requete = f"{keywords} intitle:blog" 
    
    blogs = []
    with DDGS() as ddgs:
        results = ddgs.text(requete, max_results=max_results)
        for r in results:
            blogs.append(r['href'])
            
    return blogs
