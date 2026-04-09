# Kamleshkumar Senthilkumar - 24245674
# Andoni Karafilakis - 24314657

from flask import Flask, url_for, request
from rdflib import Graph
from owlready2 import get_ontology, ThingClass
from datetime import date

# load ontology into rdflib graph
g = Graph()

# owl_path = "../ontology/yipee.owl"  
owl_path = "ontology/git_ontology_reasoned.owl"  
g.parse(owl_path)
print("Ontology loaded:", owl_path)
print("Triples loaded:", len(g))

# load ontology into owlready2
onto = get_ontology(f"file://{owl_path}").load()
IRIS = {cls.iri: cls for cls in onto.classes()}
IRIS.update({ind.iri: ind for ind in onto.individuals()})

# set the base IRI
base_iri = "http://gitontologic/knowledgerep/git#"
print("Base IRI:", base_iri)


app = Flask(__name__)

# home page
@app.route('/')
def home_page():
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<h2>CITS3005 PROJECT</h2>"
    html += "<h4>Andoni Karafilakis - 24314657</h4>"
    html += "<h4>Kamleshkumar Senthilkumar - 24245674</h4>"
    html += f"<p><b>Base IRI:</b> {base_iri}</p>"
    html += "<hr>"
    html += "<h1>Sample Queries</h1>"
    html += "<p><a href='/query1'>Repositories With > 5 Unmerged Branches</a></p>"
    html += "<p><a href='/merge-commits'>Find All Merge Commits</a></p>"
    html += "<p><a href='/concurrent-contributors'>Find Users with Concurrent Contributions to > 3 Repos</a></p>"
    html += "<p><a href='/security-commits'>All Commit Messages w/ Text 'Security' or 'Vulnerability'</a></p>"
    html += "<p><a href='/top-contributors'>Find Top Contributors per Repository</a></p>"
    html += "<p><a href='/inactive-repos'>Find Inactive Repositories (No commits in last 3+ months)</a></p>"
    html += "<p><a href='/file-types'>View and analyse the range of file type extensions</a></p>"
    html += "<hr>"
    html += "<h1>Ontology Navigator</h1>"
    html += "<p><a href='/ontology-browser'><strong>Navigate Through Individuals, Inferred Classes, Relations</strong></a></p>"
    html += "<h1>Search Feature</h1>"
    html += "<p><a href='/sparql-form'><strong>Search Procedures Using SPARQL Syntax</strong></a></p>"
    html += "<h1>Data Validation</h1>"
    html += "<p><a href='/validation'><strong>Identify any errors in Data</strong></a></p>"
    html += "<h1>Data Management</h1>"
    html += "<p><a href='/data-management'><strong>Add, Update, or Remove Data</strong></a></p>"
    html += "</body></html>"
    return html

# ALL REPOSITORIES WITH > 5 UNMERGED BRANCHES
@app.route('/query1')
def query1():

    query = '''
    PREFIX git: <http://gitontologic/knowledgerep/git#>
    SELECT ?Repository (COUNT(?Branch) AS ?branchCount)
    WHERE {
        ?Branch a git:Branch.
        ?Branch git:belongsToRepo ?Repository .
    }
    GROUP BY ?Repository
    HAVING (COUNT(?Branch) > 5)
    ORDER BY DESC(?branchCount)
    '''

    results = list(g.query(query))

    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/'>Back to Home</a></p>"
    html += "<hr>"
    html += "<h2>Query: Repositories with >5 unmerged branches</h2>"

    if not results:
        html += "<p>No repositories found.</p>"
        html += "<p>Make sure your ontology contains Branch and MainBranch individuals, "
        html += "and that Branches link to Repositories using git:belongsToRepo.</p>"
    else:
        html += "<table border=1 cellpadding=5>"
        html += "<tr><th>Repository</th><th>Branch Count</th></tr>"
        for row in results:
            repo = str(row.Repository).split("#")[-1]
            count = row.branchCount.toPython()
            html += f"<tr><td>{repo}</td><td>{count}</td></tr>"
        html += "</table>"

    html += "<p><a href='/'>Back to Home</a></p></body></html>"
    return html

# FIND ALL MERGE COMMITS more than 1 Parent
@app.route('/merge-commits')
def merge_commits():

    query = '''
    PREFIX git: <http://gitontologic/knowledgerep/git#>
    SELECT ?commit ?commitMessage ?parentCount ?branch ?commitDate ?author
    WHERE {
        ?commit a git:Commit .
        ?commit git:commit_parent_count ?parentCount .
        ?commit git:commit_message ?commitMessage .
        ?commit git:onBranch ?branch .
        ?commit git:commit_date ?commitDate .
        ?commit git:authoredBy ?author .
        FILTER(?parentCount > 1)
    }
    ORDER BY DESC(?commitDate)
    '''

    results = list(g.query(query))

    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/'>Back to Home</a></p>"
    html += "<hr>"
    html += "<h2>Query: All Merge Commits</h2>"

    if not results:
        html += "<p>No merge commits found.</p>"
    else:
        html += f"<p><b>Found {len(results)} merge commit(s):</b></p>"
        html += "<table border=1 cellpadding=5>"
        html += "<tr><th>Commit</th><th>Message</th><th>Parent Count</th><th>Branch</th><th>Date</th><th>Author</th></tr>"
        for row in results:
            commit = str(row.commit).split("#")[-1]
            message = str(row.commitMessage)[:60] + "..." if row.commitMessage and len(str(row.commitMessage)) > 60 else str(row.commitMessage) if row.commitMessage else "No message"
            parent_count = str(row.parentCount)
            branch = str(row.branch).split("#")[-1] if row.branch else "N/A"
            commit_date = str(row.commitDate)[:10] if row.commitDate else "N/A"  # Just the date part
            author = str(row.author).split("#")[-1] if row.author else "N/A"
            html += f"<tr><td>{commit}</td><td>{message}</td><td>{parent_count}</td><td>{branch}</td><td>{commit_date}</td><td>{author}</td></tr>"
        html += "</table>"

    html += "<p><a href='/'>Back to Home</a></p></body></html>"
    return html

# Users with concurrent contributons \ within 1 month?
@app.route('/concurrent-contributors')
def concurrent_contributors():
   
    query = '''
    PREFIX git: <http://gitontologic/knowledgerep/git#>
    SELECT ?user ?yearMonth (COUNT(DISTINCT ?repo) AS ?repoCount) 
    (GROUP_CONCAT(DISTINCT ?repoName; separator=", ") AS ?repositories)
    WHERE {
        ?commit a git:Commit .
        ?commit git:authoredBy ?user .
        ?commit git:onBranch ?branch.
        ?commit git:commit_date ?commitDate .
        ?branch git:belongsToRepo ?repo .
        ?repo git:repo_name ?repoName .
       
        # need to take out the month part of the date
        BIND(SUBSTR(STR(?commitDate), 1, 7) AS ?yearMonth)
    }
    GROUP BY ?user ?yearMonth
    HAVING (COUNT(DISTINCT ?repo) >= 3)
    ORDER BY DESC(?repoCount) ?user ?yearMonth
    '''

    results = list(g.query(query))

    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/'>Back to Home</a></p>"
    html += "<hr>"
    html += "<h2>Query: Users with Concurrent Contributions to 3+ Repositories</h2>"
    html += "<p><i>Concurrent = contributions made in the same month</i></p>"

    if not results:
        html += "<p>No users found with concurrent contributions to 3+ repositories.</p>"
    else:
        html += f"<p><b>Found {len(results)} user-month combinations with 3+ repository contributions:</b></p>"
        html += "<table border=1 cellpadding=5>"
        html += "<tr><th>User</th><th>Month</th><th>Repo Count</th><th>Repository Names</th></tr>"
        for row in results:
            user = str(row.user).split("#")[-1]
            year_month = str(row.yearMonth)
            repo_count = str(row.repoCount)
            repos = str(row.repositories) if row.repositories else "N/A"
            html += f"<tr><td>{user}</td><td>{year_month}</td><td>{repo_count}</td><td>{repos}</td></tr>"
        html += "</table>"

    html += "<p><a href='/'>Back to Home</a></p></body></html>"
    return html

# Security/Vulnerability in Commit Messages
@app.route('/security-commits')
def security_commits():
   
    query = '''
    PREFIX git: <http://gitontologic/knowledgerep/git#>
    SELECT ?commit ?commitMessage ?branch ?author ?commitDate ?repo ?repoName
    WHERE {
        ?commit a git:Commit .
        ?commit git:commit_message ?commitMessage .
        ?commit git:onBranch ?branch .
        ?commit git:authoredBy ?author .
        ?commit git:commit_date ?commitDate .
        ?branch git:belongsToRepo ?repo .
        ?repo git:repo_name ?repoName .
        
        # check for security stuff - case insensitve
        FILTER(CONTAINS(LCASE(?commitMessage), "security") || CONTAINS(LCASE(?commitMessage), "vulnerability"))
    }
    ORDER BY DESC(?commitDate)
    '''

    results = list(g.query(query))

    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/'>Back to Home</a></p>"
    html += "<hr>"
    html += "<h2>Security-Related Commits</h2>"
    html += "<p><i>Searching for commits containing: security or vulnerability</i></p>"

    if not results:
        html += "<p>No security-related commits found.</p>"
    else:
        html += f"<p><b>Found {len(results)} security-related commit(s):</b></p>"
        html += "<table border=1 cellpadding=5 style='width:100%;'>"
        html += "<tr style='background:#e0e0e0;'><th>Commit</th><th>Message</th><th>Branch</th><th>Author</th><th>Date</th><th>Repository</th></tr>"
       
        for row in results:
            commit = str(row.commit).split("#")[-1]
            message = str(row.commitMessage)
           
            # Truncate long messages
            if len(message) > 180:
                message = message[:180] + "... Commit Message Too Long To Display"
           
            branch = str(row.branch).split("#")[-1] if row.branch else "N/A"
            author = str(row.author).split("#")[-1] if row.author else "N/A"
            commit_date = str(row.commitDate)[:16] if row.commitDate else "N/A"  # Date and time
            repo_name = str(row.repoName) if row.repoName else "N/A"
           
            html += f"<tr><td style='font-family:monospace;'>{commit}</td><td>{message}</td><td>{branch}</td><td>{author}</td><td>{commit_date}</td><td>{repo_name}</td></tr>"
        html += "</table>"

    html += "<p><a href='/'>Back to Home</a></p></body></html>"
    return html

# Top contributors per repo. measured iin number of commits
@app.route('/top-contributors')
def top_contributors():
    query = '''
    PREFIX git: <http://gitontologic/knowledgerep/git#>
    SELECT ?repoName ?user ?userName (COUNT(?commit) AS ?commitCount)
    WHERE {
        ?commit a git:Commit .
        ?commit git:authoredBy ?user .
        ?commit git:onBranch ?branch .
        ?branch git:belongsToRepo ?repo .
        ?repo git:repo_name ?repoName .
        OPTIONAL { ?user git:user_name ?userName }
    }
    GROUP BY ?repoName ?user ?userName
    ORDER BY ?repoName DESC(?commitCount)
    '''

    results = list(g.query(query))

    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/'>Back to Home</a></p>"
    html += "<hr>"
    html += "<h2>Top Contributors per Repository</h2>"
    html += "<p><i>Ranked by number of commits authored per repository</i></p>"

    if not results:
        html += "<p>No contributors found.</p>"
    else:
        html += f"<p><b>Found contributors across repositories:</b></p>"
        html += "<table border=1 cellpadding=5 style='width:100%;'>"
        html += "<tr style='background:#e0e0e0;'><th>Rank</th><th>Repository</th><th>User</th><th>User Name</th><th>Commit Count</th></tr>"
       
        # Group results by repository for ranking
        repos = {}
        for row in results:
            repo_name = str(row.repoName) if row.repoName else "Unknown"
            if repo_name not in repos:
                repos[repo_name] = []
            repos[repo_name].append({
                'user': str(row.user).split("#")[-1] if row.user else "Unknown",
                'user_name': str(row.userName) if row.userName else str(row.user).split("#")[-1] if row.user else "Unknown",
                'commit_count': int(row.commitCount)
            })
        
        # Sort contributors within each repo by commit count and take only top 3
        for repo_name in repos:
            repos[repo_name].sort(key=lambda x: x['commit_count'], reverse=True)
            repos[repo_name] = repos[repo_name][:3]  # Keep only top 3
        
        # display results 
        current_repo = None
        for repo_name in sorted(repos.keys()):
            contributors = repos[repo_name]
            
            for rank, contributor in enumerate(contributors, 1):
                # Add visual separator between repositories
                if current_repo != repo_name:
                    if current_repo is not None:
                        html += "<tr><td colspan='5' style='background:#f0f0f0; height:5px;'></td></tr>"
                    current_repo = repo_name
                
                html += f"<tr>"
                html += f"<td>#{rank}</td>"
                html += f"<td><strong>{repo_name}</strong></td>"
                html += f"<td>{contributor['user']}</td>"
                html += f"<td>{contributor['user_name']}</td>"
                html += f"<td>{contributor['commit_count']}</td>"
                html += "</tr>"
        html += "</table>"

    html += "<p><a href='/'>Back to Home</a></p></body></html>"
    return html

# Query to find inactive repos
@app.route('/inactive-repos')
def inactive_repos():
    current_date = date.today().strftime('%Y-%m-%d')
   
    query = '''
    PREFIX git: <http://gitontologic/knowledgerep/git#>
    SELECT ?repo ?repoName (MAX(?commitDate) AS ?lastCommitDate) (COUNT(?commit) AS ?totalCommits)
    WHERE {
        ?repo a git:Repository .
        ?repo git:repo_name ?repoName .
        ?commit a git:Commit .
        ?commit git:onBranch ?branch .
        ?commit git:commit_date ?commitDate .
        ?branch git:belongsToRepo ?repo .
    }
    GROUP BY ?repo ?repoName
    ORDER BY DESC(?lastCommitDate)
    '''

    

    results = list(g.query(query))

    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/'>Back to Home</a></p>"
    html += "<hr>"
    html += "<h2>Inactive Repositories</h2>"
    html += f"<p><i>Repositories with no commits for more than 3 months (90+ days from {current_date})</i></p>"

    # Filter results to only show inactive repos (>90 days) and calculate days since last commit
    from datetime import datetime
    current_date_obj = datetime.strptime(current_date, '%Y-%m-%d')
    inactive_results = []
    
    for row in results:
        if row.lastCommitDate:
            try:
                
                last_commit_str = str(row.lastCommitDate)[:10]  # just the date part
                last_commit_obj = datetime.strptime(last_commit_str, '%Y-%m-%d')
                days_since = (current_date_obj - last_commit_obj).days
                
                # only repos inactive for more than 90 days
                if days_since > 90:
                    inactive_results.append({
                        'repo_name': str(row.repoName) if row.repoName else "Unknown",
                        'last_commit_date': last_commit_str,
                        'days_since': days_since,
                        'total_commits': int(row.totalCommits) if row.totalCommits else 0
                    })
            except:
                continue
    
    # Sort by days since last commit
    inactive_results.sort(key=lambda x: x['days_since'], reverse=True)

    if not inactive_results:
        html += "<p>No inactive repositories found - all repositories have recent activity!</p>"
    else:
        html += f"<p><b>Found {len(inactive_results)} inactive repository/repositories:</b></p>"
        html += "<table border=1 cellpadding=5 style='width:100%;'>"
        html += "<tr style='background:#e0e0e0;'><th>Repository</th><th>Last Commit Date</th><th>Days Since Last Commit</th><th>Total Commits</th><th>Status</th></tr>"
       
        for repo_data in inactive_results:
            repo_name = repo_data['repo_name']
            last_commit_date = repo_data['last_commit_date']
            days_since = repo_data['days_since']
            total_commits = repo_data['total_commits']
            
            status = "Inactive"
            if days_since > 365:  # More than 1 year
                status = "Very Inactive (>1 year)"
            elif days_since > 180:  # More than 6 months
                status = "Quite Inactive (>6 months)"
            else:  # 3-6 months
                status = "Inactive (>3 months)"
           
            html += f"<tr>"
            html += f"<td><strong>{repo_name}</strong></td>"
            html += f"<td>{last_commit_date}</td>"
            html += f"<td>{days_since}</td>"
            html += f"<td>{total_commits}</td>"
            html += f"<td>{status}</td>"
            html += "</tr>"
        html += "</table>"
       

    html += "<p><a href='/'>Back to Home</a></p></body></html>"
    return html

#check out the different types of files in each repository
@app.route('/file-types')
def file_types():
    query = '''
    PREFIX git: <http://gitontologic/knowledgerep/git#>
    SELECT ?extension (COUNT(?file) AS ?fileCount) (GROUP_CONCAT(DISTINCT ?repoName; separator=", ") AS ?repositories)
    WHERE {
        ?file a git:File .
        ?file git:file_name ?fileName .
        ?file git:fileOfRepo ?repo .
        ?repo git:repo_name ?repoName .
        
        # Find file extension
        BIND(REPLACE(?fileName, "^.*\\\\.", "") AS ?extension)
        
        # no files without extensions
        FILTER(?extension != "" && ?extension != ?fileName)
    }
    GROUP BY ?extension
    ORDER BY DESC(?fileCount)
    '''

    results = list(g.query(query))

    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/'>Back to Home</a></p>"
    html += "<hr>"
    html += "<h2>File Types Analysis</h2>"
    html += "<p><i>Distribution of file types by extension across all repositories</i></p>"

    if not results:
        html += "<p>No files with extensions found.</p>"
        html += "<p>This could mean:</p>"
        html += "<ul>"
        html += "<li>Files don't have extensions in their names</li>"
        html += "<li>File names might not be properly stored</li>"
        html += "<li>The git:file_name property might be missing</li>"
        html += "</ul>"
        
        # Show some sample file names for debugging
        debug_query = '''
        PREFIX git: <http://gitontologic/knowledgerep/git#>
        SELECT ?fileName ?repoName
        WHERE {
            ?file a git:File .
            ?file git:file_name ?fileName .
            ?file git:fileOfRepo ?repo .
            ?repo git:repo_name ?repoName .
        }
        LIMIT 10
        '''
        
        debug_results = list(g.query(debug_query))
        if debug_results:
            html += "<h3>Sample file names (for debugging):</h3>"
            html += "<table border=1 cellpadding=5>"
            html += "<tr><th>File Name</th><th>Repository</th></tr>"
            for row in debug_results:
                file_name = str(row.fileName) if row.fileName else "N/A"
                repo_name = str(row.repoName) if row.repoName else "N/A"
                html += f"<tr><td>{file_name}</td><td>{repo_name}</td></tr>"
            html += "</table>"
    else:
        total_files = sum(int(row.fileCount) for row in results)
        html += f"<p><b>Found {len(results)} different file types across {total_files} total files:</b></p>"
        
        html += "<table border=1 cellpadding=5 style='width:100%;'>"
        html += "<tr style='background:#e0e0e0;'><th>File Extension</th><th>Count</th><th>Percentage</th><th>Repositories Found In</th></tr>"
       
        for row in results:
            extension = str(row.extension) if row.extension else "Unknown"
            file_count = int(row.fileCount)
            percentage = round((file_count / total_files) * 100, 1) if total_files > 0 else 0
            repositories = str(row.repositories) if row.repositories else "N/A"
            
            html += f"<tr>"
            html += f"<td><strong>.{extension}</strong></td>"
            html += f"<td>{file_count}</td>"
            html += f"<td>{percentage}%</td>"
            html += f"<td>{repositories}</td>"
            html += "</tr>"
        html += "</table>"
        


    html += "<p><a href='/'>Back to Home</a></p></body></html>"
    return html

# routes for browsing ontology
@app.route('/ontology-browser')
def ontology_browser():
    # shows all classes and individuals 
    page = int(request.args.get('page', 1))
    per_page = 50  # 50 per page
   
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/'>Back to Home</a></p>"
    html += "<hr>"
    html += "<h2>Ontology Browser</h2>"
   
    # classes section 
    html += "<h3>Classes</h3>"
    html += "<div style='background:#f9f9f9; padding:10px; margin:10px 0; border-radius:5px;'>"
    for cls in onto.classes():
        # Calculate instance count, including special handling for commit classes
        instance_count = 0
       
        if cls.name == "InitialCommit":
            # Count commits with is_initial=true
            for ind in onto.individuals():
                if hasattr(ind, 'is_initial') and getattr(ind, 'is_initial', False):
                    instance_count += 1
        elif cls.name == "MergeCommit":
            # Count commits with commit_parent_count > 1
            for ind in onto.individuals():
                if hasattr(ind, 'commit_parent_count'):
                    parent_count = getattr(ind, 'commit_parent_count', 0)
                    if parent_count and parent_count > 1:
                        instance_count += 1
        elif cls.name == "NormalCommit":
            # Count commits that are not initial and not merge
            for ind in onto.individuals():
                if hasattr(ind, 'commit_parent_count') and hasattr(ind, 'is_initial'):
                    is_initial = getattr(ind, 'is_initial', True)
                    parent_count = getattr(ind, 'commit_parent_count', 0)
                    if not is_initial and parent_count == 1:
                        instance_count += 1
        elif cls.name == "MainBranch":
            # Count branches with is_default=true (only look at actual Branch instances)
            branch_class = None
            for cls_obj in onto.classes():
                if cls_obj.name == "Branch":
                    branch_class = cls_obj
                    break
            if branch_class:
                for ind in branch_class.instances():
                    if hasattr(ind, 'is_default') and getattr(ind, 'is_default', False):
                        instance_count += 1
        elif cls.name == "SecondaryBranch":
            # Count branches with is_default=false (only look at actual Branch instances)
            branch_class = None
            for cls_obj in onto.classes():
                if cls_obj.name == "Branch":
                    branch_class = cls_obj
                    break
            if branch_class:
                for ind in branch_class.instances():
                    if hasattr(ind, 'is_default') and not getattr(ind, 'is_default', True):
                        instance_count += 1
        else:
            # Regular direct instances for other classes
            instance_count = len(list(cls.instances()))
       
        # Show instance count with appropriate label
        if cls.name in ["InitialCommit", "MergeCommit", "NormalCommit", "MainBranch", "SecondaryBranch"]:
            html += f"<p><a href='{url_for('class_page', iri=cls.iri)}'>{cls.name}</a> - {instance_count} instances (by properties)</p>"
        else:
            html += f"<p><a href='{url_for('class_page', iri=cls.iri)}'>{cls.name}</a> - {instance_count} direct instances</p>"
    html += "</div>"
   
    # Relations section
    html += "<h3>Relations (Object Properties)</h3>"
    html += "<div style='background:#f9f9f9; padding:10px; margin:10px 0; border-radius:5px;'>"
   
    # List of all relations
    relations = [
        "authoredBy",
        "committedBy",
        "onBranch",
        "contributesTo",
        "ownsCommit",
        "belongsToRepo",
        "hasContributors",
        "hasBranch",
        "fileOfRepo",
        "hasChildCommit",
        "hasParentCommit",
        "hasCommit",
        "taggedAs"
    ]
   
    for relation in relations:
        # Create placeholder links for relations (will implement relation pages later)
        html += f"<p><a href='/relation/{relation}'>{relation}</a></p>"
   
    html += "</div>"
   
    # Individuals section with pagination
    html += "<h3>Individuals (Every Individual in Graph)</h3>"
    all_individuals = list(onto.individuals())
    total_individuals = len(all_individuals)
    total_pages = max(1, (total_individuals + per_page - 1) // per_page)
   
    html += f"<p>Total: <strong>{total_individuals}</strong> individuals</p>"
   
    if total_individuals > 0:
        if total_pages > 1:
            html += f"<p>Page <strong>{page}</strong> of <strong>{total_pages}</strong> (showing {per_page} per page)</p>"
           
            # Pagination links at top
            html += "<div style='margin:10px 0;'>"
            if page > 1:
                html += f"<a href='?page={page-1}' style='margin-right:10px;'>Previous</a>"
           
            start_page = max(1, page - 2)
            end_page = min(total_pages, page + 2)
           
            for p in range(start_page, end_page + 1):
                if p == page:
                    html += f"<strong style='margin:0 5px;'>{p}</strong>"
                else:
                    html += f"<a href='?page={p}' style='margin:0 5px;'>{p}</a>"
           
            if page < total_pages:
                html += f"<a href='?page={page+1}' style='margin-left:10px;'>Next →</a>"
            html += "</div>"
       
        # Calculate which individuals to show
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        display_individuals = all_individuals[start_idx:end_idx]
       
        html += "<div style='background:#f9f9f9; padding:10px; margin:10px 0; border-radius:5px;'>"
        for ind in display_individuals:
            html += f"<p><a href='{url_for('individual_page', iri=ind.iri)}'>{ind.name}</a></p>"
        html += "</div>"
       
        # Repeat pagination links at bottom if more than 1 page
        if total_pages > 1:
            html += "<div style='margin:10px 0;'>"
            if page > 1:
                html += f"<a href='?page={page-1}' style='margin-right:10px;'>Previous</a>"
           
            for p in range(start_page, end_page + 1):
                if p == page:
                    html += f"<strong style='margin:0 5px;'>{p}</strong>"
                else:
                    html += f"<a href='?page={p}' style='margin:0 5px;'>{p}</a>"
           
            if page < total_pages:
                html += f"<a href='?page={page+1}' style='margin-left:10px;'>Next →</a>"
            html += "</div>"
   
    html += "<p><a href='/'>Back to Home</a></p>"
    html += "</body></html>"
    return html

@app.route('/class/<path:iri>')
def class_page(iri):
    # shows info about a specific class
    if iri not in IRIS:
        return f"<html><body><h2>Class not found: {iri}</h2><p><a href='/ontology-browser'>Back to Browser</a></p></body></html>"
   
    Class = IRIS[iri]
    page = int(request.args.get('page', 1))
    per_page = 25  # Show 25 individuals per page
   
    html = f"<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/ontology-browser'>Back to Browser</a> | <a href='/'>Home</a></p>"
    html += "<hr>"
    html += f"<h2>Class: {Class.name}</h2>"
    html += f"<p><strong>IRI:</strong> {Class.iri}</p>"

    # Superclasses
    html += "<h3>Superclasses</h3>"
    if Class.is_a:
        for sup in Class.is_a:
            if isinstance(sup, ThingClass):
                html += f"<p><a href='{url_for('class_page', iri=sup.iri)}'>{sup.name}</a></p>"
            else:
                html += f"<p>{sup}</p>"
    else:
        html += "<p>None</p>"

    # Subclasses
    html += "<h3>Subclasses</h3>"
    subclasses = list(Class.subclasses())
    if subclasses:
        for sub in subclasses:
            html += f"<p><a href='{url_for('class_page', iri=sub.iri)}'>{sub.name}</a></p>"
    else:
        html += "<p>None</p>"

    # Instances with pagination
    html += "<h3>Individuals</h3>"
   
    # get all individuals for this class
    all_individuals = []
   
    # Special handling for InitialCommit class - find commits with is_initial=true
    if Class.name == "InitialCommit":
        for ind in onto.individuals():
            if hasattr(ind, 'is_initial') and getattr(ind, 'is_initial', False):
                all_individuals.append(ind)
   
    # Special handling for MergeCommit class - find commits with commit_parent_count > 1
    elif Class.name == "MergeCommit":
        for ind in onto.individuals():
            if hasattr(ind, 'commit_parent_count'):
                parent_count = getattr(ind, 'commit_parent_count', 0)
                if parent_count and parent_count > 1:
                    all_individuals.append(ind)
   
    # Special handling for NormalCommit class - find commits that are not initial and not merge
    elif Class.name == "NormalCommit":
        for ind in onto.individuals():
            if hasattr(ind, 'commit_parent_count') and hasattr(ind, 'is_initial'):
                is_initial = getattr(ind, 'is_initial', True)
                parent_count = getattr(ind, 'commit_parent_count', 0)
                if not is_initial and parent_count == 1:
                    all_individuals.append(ind)
   
    # Special handling for MainBranch class - find branches with is_default=true
    elif Class.name == "MainBranch":
        # Only look at actual Branch instances
        branch_class = None
        for cls_obj in onto.classes():
            if cls_obj.name == "Branch":
                branch_class = cls_obj
                break
        if branch_class:
            for ind in branch_class.instances():
                if hasattr(ind, 'is_default') and getattr(ind, 'is_default', False):
                    all_individuals.append(ind)
   
    # Special handling for SecondaryBranch class - find branches with is_default=false
    elif Class.name == "SecondaryBranch":
        # Only look at actual Branch instances
        branch_class = None
        for cls_obj in onto.classes():
            if cls_obj.name == "Branch":
                branch_class = cls_obj
                break
        if branch_class:
            for ind in branch_class.instances():
                if hasattr(ind, 'is_default') and not getattr(ind, 'is_default', True):
                    all_individuals.append(ind)
   
    # Regular instances for other classes
    else:
        all_individuals = list(Class.instances())
   
    total_individuals = len(all_individuals)
   
    if total_individuals > 0:
        total_pages = max(1, (total_individuals + per_page - 1) // per_page)
       
        # Add pagination info and links
        html += f"<p>Found <strong>{total_individuals}</strong> individuals"
        if Class.name in ["InitialCommit", "MergeCommit", "NormalCommit", "MainBranch", "SecondaryBranch"]:
            html += f" (identified by properties)"
        html += "</p>"
       
        if total_pages > 1:
            html += f"<p>Page <strong>{page}</strong> of <strong>{total_pages}</strong> (showing {per_page} per page)</p>"
           
            # Pagination links at top
            html += "<div style='margin:10px 0;'>"
            if page > 1:
                html += f"<a href='?page={page-1}' style='margin-right:10px;'>Previous</a>"
           
            start_page = max(1, page - 2)
            end_page = min(total_pages, page + 2)
           
            for p in range(start_page, end_page + 1):
                if p == page:
                    html += f"<strong style='margin:0 5px;'>{p}</strong>"
                else:
                    html += f"<a href='?page={p}' style='margin:0 5px;'>{p}</a>"
           
            if page < total_pages:
                html += f"<a href='?page={page+1}' style='margin-left:10px;'>Next →</a>"
            html += "</div>"
       
        # Calculate which individuals to show
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        display_individuals = all_individuals[start_idx:end_idx]
       
        # Display individuals
        html += "<div style='background:#f9f9f9; padding:10px; margin:10px 0; border-radius:5px;'>"
        for ind in display_individuals:
            html += f"<p><a href='{url_for('individual_page', iri=ind.iri)}'>{ind.name}</a></p>"
        html += "</div>"
       
        # Repeat pagination links at bottom if more than 1 page
        if total_pages > 1:
            html += "<div style='margin:10px 0;'>"
            if page > 1:
                html += f"<a href='?page={page-1}' style='margin-right:10px;'>Previous</a>"
           
            for p in range(start_page, end_page + 1):
                if p == page:
                    html += f"<strong style='margin:0 5px;'>{p}</strong>"
                else:
                    html += f"<a href='?page={p}' style='margin:0 5px;'>{p}</a>"
           
            if page < total_pages:
                html += f"<a href='?page={page+1}' style='margin-left:10px;'>Next →</a>"
            html += "</div>"
    else:
        html += "<p>No individuals found</p>"

    html += "<p><a href='/ontology-browser'>Back to Browser</a> | <a href='/'>Back to Home</a></p>"
    html += "</body></html>"
    return html

@app.route('/individual/<path:iri>')
def individual_page(iri):
    # shows details for one individual
    if iri not in IRIS:
        return f"<html><body><h2>Individual not found: {iri}</h2><p><a href='/ontology-browser'>Back to Browser</a></p></body></html>"
   
    individual = IRIS[iri]
    html = f"<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/ontology-browser'>Back to Browser</a> | <a href='/'>Home</a></p>"
    html += "<hr>"
    html += f"<h2>Individual: {individual.name}</h2>"
    html += f"<p><strong>IRI:</strong> {individual.iri}</p>"

    # Classes (types)
    html += "<h3>Types (Classes)</h3>"
    if individual.is_a:
        for cls in individual.is_a:
            if isinstance(cls, ThingClass):
                html += f"<p><a href='{url_for('class_page', iri=cls.iri)}'>{cls.name}</a></p>"
            else:
                html += f"<p>{cls}</p>"
    else:
        html += "<p>None</p>"

    # Properties
    html += "<h3>Properties</h3>"
    html += "<table border='1' cellpadding='5' style='border-collapse:collapse;'>"
    html += "<tr style='background:#e0e0e0;'><th>Property</th><th>Value</th></tr>"
   
    has_properties = False
    for prop in onto.properties():
        try:
            values = getattr(individual, prop.name, None)
            if values:
                has_properties = True
                if isinstance(values, list):
                    for value in values:
                        if hasattr(value, 'iri') and value.iri in IRIS:
                            # Link to other individuals/classes
                            if isinstance(value, ThingClass):
                                html += f"<tr><td>{prop.name}</td><td><a href='{url_for('class_page', iri=value.iri)}'>{value.name}</a></td></tr>"
                            else:
                                html += f"<tr><td>{prop.name}</td><td><a href='{url_for('individual_page', iri=value.iri)}'>{value.name}</a></td></tr>"
                        else:
                            html += f"<tr><td>{prop.name}</td><td>{value}</td></tr>"
                else:
                    if hasattr(values, 'iri') and values.iri in IRIS:
                        # Link to other individuals/classes
                        if isinstance(values, ThingClass):
                            html += f"<tr><td>{prop.name}</td><td><a href='{url_for('class_page', iri=values.iri)}'>{values.name}</a></td></tr>"
                        else:
                            html += f"<tr><td>{prop.name}</td><td><a href='{url_for('individual_page', iri=values.iri)}'>{values.name}</a></td></tr>"
                    else:
                        html += f"<tr><td>{prop.name}</td><td>{values}</td></tr>"
        except:
            continue
   
    if not has_properties:
        html += "<tr><td colspan='2'>No properties found</td></tr>"
   
    html += "</table>"

    html += "<p><a href='/ontology-browser'>Back to Browser</a> | <a href='/'>Back to Home</a></p>"
    html += "</body></html>"
    return html

@app.route('/relation/<relation_name>')
def relation_page(relation_name):
    """Display domain to range mappings for a specific relation with pagination"""
    page = int(request.args.get('page', 1))
    per_page = 25  # Show 25 mappings per page
   
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/ontology-browser'>Back to Browser</a> | <a href='/'>Home</a></p>"
    html += "<hr>"
    html += f"<h2>Relation: {relation_name}</h2>"
    html += f"<p><strong>Property:</strong> {base_iri}{relation_name}</p>"
   
    # Collect all domain->range mappings for this relation
    mappings = []
   
    # Look for the property in the ontology
    relation_property = None
    for prop in onto.properties():
        if prop.name == relation_name:
            relation_property = prop
            break
   
    if relation_property:
        # Go through all individuals and find those that have this property
        for individual in onto.individuals():
            try:
                # get the property values for this individual
                property_values = getattr(individual, relation_name, None)
                if property_values:
                    # handle single values and lists
                    if isinstance(property_values, list):
                        for value in property_values:
                            mappings.append((individual, value))
                    else:
                        mappings.append((individual, property_values))
            except:
                continue
   

   
    total_mappings = len(mappings)
   
    if total_mappings > 0:
        total_pages = max(1, (total_mappings + per_page - 1) // per_page)
       
        html += f"<p>Found <strong>{total_mappings}</strong> domain→range mappings for this relation</p>"
       
        if total_pages > 1:
            html += f"<p>Page <strong>{page}</strong> of <strong>{total_pages}</strong> (showing {per_page} per page)</p>"
           
            # Pagination links at top
            html += "<div style='margin:10px 0;'>"
            if page > 1:
                html += f"<a href='?page={page-1}' style='margin-right:10px;'>Previous</a>"
           
            start_page = max(1, page - 2)
            end_page = min(total_pages, page + 2)
           
            for p in range(start_page, end_page + 1):
                if p == page:
                    html += f"<strong style='margin:0 5px;'>{p}</strong>"
                else:
                    html += f"<a href='?page={p}' style='margin:0 5px;'>{p}</a>"
           
            if page < total_pages:
                html += f"<a href='?page={page+1}' style='margin-left:10px;'>Next →</a>"
            html += "</div>"
       
        # Calculate which mappings to show
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        display_mappings = mappings[start_idx:end_idx]
       
        # Create the domain→range table
        html += "<table border='1' cellpadding='8' style='border-collapse:collapse; width:100%;'>"
        html += "<tr style='background:#e0e0e0;'>"
        html += "<th style='width:45%;'>Domain (Subject)</th>"
        html += "<th style='width:10%; text-align:center;'>→</th>"
        html += "<th style='width:45%;'>Range (Object)</th>"
        html += "</tr>"
       
        for domain, range_obj in display_mappings:
            # Domain column - link to individual if it's in our IRIS
            if hasattr(domain, 'iri') and domain.iri in IRIS:
                domain_link = f"<a href='{url_for('individual_page', iri=domain.iri)}'>{domain.name}</a>"
            else:
                domain_link = str(domain)
           
            # Range column - link to individual if it's in our IRIS  
            if hasattr(range_obj, 'iri') and range_obj.iri in IRIS:
                range_link = f"<a href='{url_for('individual_page', iri=range_obj.iri)}'>{range_obj.name}</a>"
            elif hasattr(range_obj, 'name'):
                range_link = str(range_obj.name)
            else:
                range_link = str(range_obj)
           
            html += f"<tr>"
            html += f"<td>{domain_link}</td>"
            html += f"<td style='text-align:center; font-weight:bold; color:#666;'>→</td>"
            html += f"<td>{range_link}</td>"
            html += "</tr>"
       
        html += "</table>"
       
        # Repeat pagination links at bottom
        if total_pages > 1:
            html += "<div style='margin:10px 0;'>"
            if page > 1:
                html += f"<a href='?page={page-1}' style='margin-right:10px;'>Previous</a>"
           
            for p in range(start_page, end_page + 1):
                if p == page:
                    html += f"<strong style='margin:0 5px;'>{p}</strong>"
                else:
                    html += f"<a href='?page={p}' style='margin:0 5px;'>{p}</a>"
           
            if page < total_pages:
                html += f"<a href='?page={page+1}' style='margin-left:10px;'>Next →</a>"
            html += "</div>"
   
    else:
        html += "<p>No mappings found for this relation.</p>"
   
    html += "<p><a href='/ontology-browser'>Back to Browser</a> | <a href='/'>Home</a></p>"
    html += "</body></html>"
    return html

@app.route('/initial-commits')
def initial_commits():
    """Show all initial commits based on is_initial property with pagination"""
    page = int(request.args.get('page', 1))
    per_page = 25  # Show 25 commits per page
   
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/ontology-browser'>Back to Browser</a> | <a href='/'>Home</a></p>"
    html += "<hr>"
    html += "<h2>Initial Commits</h2>"
   
    initial_commits = []
    for ind in onto.individuals():
        if hasattr(ind, 'is_initial') and getattr(ind, 'is_initial', False):
            initial_commits.append(ind)
   
    total_commits = len(initial_commits)
    total_pages = max(1, (total_commits + per_page - 1) // per_page)  # Ceiling division, min 1
   
    html += f"<p>Found <strong>{total_commits}</strong> initial commits (where is_initial = true)</p>"
   
    if total_commits > 0:
        html += f"<p>Page <strong>{page}</strong> of <strong>{total_pages}</strong> (showing {per_page} per page)</p>"
       
        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        display_commits = initial_commits[start_idx:end_idx]
       
        # Pagination links (only show if more than 1 page)
        if total_pages > 1:
            html += "<div style='margin:10px 0;'>"
            if page > 1:
                html += f"<a href='?page={page-1}' style='margin-right:10px;'>Previous</a>"
           
            # Show page numbers (show current page and 2 before/after)
            start_page = max(1, page - 2)
            end_page = min(total_pages, page + 2)
           
            for p in range(start_page, end_page + 1):
                if p == page:
                    html += f"<strong style='margin:0 5px;'>{p}</strong>"
                else:
                    html += f"<a href='?page={p}' style='margin:0 5px;'>{p}</a>"
           
            if page < total_pages:
                html += f"<a href='?page={page+1}' style='margin-left:10px;'>Next →</a>"
            html += "</div>"
       
        html += "<table border='1' cellpadding='5' style='border-collapse:collapse;'>"
        html += "<tr style='background:#e0e0e0;'><th>Commit</th><th>Message</th><th>Date</th><th>Author</th><th>Repository</th></tr>"
       
        for commit in display_commits:
            message = getattr(commit, 'commit_message', 'N/A')
            if len(message) > 100:
                message = message[:100] + "..."
           
            date = getattr(commit, 'commit_date', 'N/A')
            if date != 'N/A':
                date = str(date)[:16]  # Just date and time part
           
            author = 'N/A'
            if hasattr(commit, 'authoredBy') and commit.authoredBy:
                author = commit.authoredBy[0].name if isinstance(commit.authoredBy, list) else commit.authoredBy.name
           
            # Try to find repository through branch
            repo = 'N/A'
            if hasattr(commit, 'onBranch') and commit.onBranch:
                branch = commit.onBranch[0] if isinstance(commit.onBranch, list) else commit.onBranch
                if hasattr(branch, 'belongsToRepo') and branch.belongsToRepo:
                    repo_obj = branch.belongsToRepo[0] if isinstance(branch.belongsToRepo, list) else branch.belongsToRepo
                    repo = getattr(repo_obj, 'repo_name', repo_obj.name)
           
            html += f"<tr>"
            html += f"<td><a href='{url_for('individual_page', iri=commit.iri)}'>{commit.name}</a></td>"
            html += f"<td>{message}</td>"
            html += f"<td>{date}</td>"
            html += f"<td>{author}</td>"
            html += f"<td>{repo}</td>"
            html += "</tr>"
       
        html += "</table>"
       
        # Repeat pagination links at bottom
        if total_pages > 1:
            html += "<div style='margin:10px 0;'>"
            if page > 1:
                html += f"<a href='?page={page-1}' style='margin-right:10px;'>Previous</a>"
           
            for p in range(start_page, end_page + 1):
                if p == page:
                    html += f"<strong style='margin:0 5px;'>{p}</strong>"
                else:
                    html += f"<a href='?page={p}' style='margin:0 5px;'>{p}</a>"
           
            if page < total_pages:
                html += f"<a href='?page={page+1}' style='margin-left:10px;'>Next →</a>"
            html += "</div>"
           
    else:
        html += "<p>No initial commits found.</p>"
   
    html += "<p><a href='/ontology-browser'>Back to Browser</a> | <a href='/'>Back to Home</a></p>"
    html += "</body></html>"
    return html

@app.route('/normal-commits')
def normal_commits():
    """Show all normal commits (not initial, not merge) with pagination"""
    page = int(request.args.get('page', 1))
    per_page = 25  # Show 25 commits per page
   
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/ontology-browser'>Back to Browser</a> | <a href='/'>Home</a></p>"
    html += "<hr>"
    html += "<h2>Normal Commits</h2>"
   
    normal_commits = []
    for ind in onto.individuals():
        # Check if it's a commit with the required properties
        if hasattr(ind, 'commit_parent_count') and hasattr(ind, 'is_initial'):
            is_initial = getattr(ind, 'is_initial', True)
            parent_count = getattr(ind, 'commit_parent_count', 0)
           
            # Normal commit: not initial AND has exactly 1 parent
            if not is_initial and parent_count == 1:
                normal_commits.append(ind)
   
    total_commits = len(normal_commits)
    total_pages = (total_commits + per_page - 1) // per_page  # Ceiling division
   
    html += f"<p>Found <strong>{total_commits}</strong> normal commits (is_initial=false AND commit_parent_count=1)</p>"
    html += f"<p>Page <strong>{page}</strong> of <strong>{total_pages}</strong> (showing {per_page} per page)</p>"
   
    if normal_commits:
        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        display_commits = normal_commits[start_idx:end_idx]
       
        # Pagination links
        if total_pages > 1:
            html += "<div style='margin:10px 0;'>"
            if page > 1:
                html += f"<a href='?page={page-1}' style='margin-right:10px;'>Previous</a>"
           
            # Show page numbers (show current page and 2 before/after)
            start_page = max(1, page - 2)
            end_page = min(total_pages, page + 2)
           
            for p in range(start_page, end_page + 1):
                if p == page:
                    html += f"<strong style='margin:0 5px;'>{p}</strong>"
                else:
                    html += f"<a href='?page={p}' style='margin:0 5px;'>{p}</a>"
           
            if page < total_pages:
                html += f"<a href='?page={page+1}' style='margin-left:10px;'>Next →</a>"
            html += "</div>"
       
        html += "<table border='1' cellpadding='5' style='border-collapse:collapse;'>"
        html += "<tr style='background:#e0e0e0;'><th>Commit</th><th>Message</th><th>Date</th><th>Author</th><th>Parents</th></tr>"
       
        for commit in display_commits:
            message = getattr(commit, 'commit_message', 'N/A')
            if len(message) > 80:
                message = message[:80] + "..."
           
            date = getattr(commit, 'commit_date', 'N/A')
            if date != 'N/A':
                date = str(date)[:16]  # Just date and time part
           
            author = 'N/A'
            if hasattr(commit, 'authoredBy') and commit.authoredBy:
                author = commit.authoredBy[0].name if isinstance(commit.authoredBy, list) else commit.authoredBy.name
           
            parent_count = getattr(commit, 'commit_parent_count', 0)
           
            html += f"<tr>"
            html += f"<td><a href='{url_for('individual_page', iri=commit.iri)}'>{commit.name}</a></td>"
            html += f"<td>{message}</td>"
            html += f"<td>{date}</td>"
            html += f"<td>{author}</td>"
            html += f"<td>{parent_count}</td>"
            html += "</tr>"
       
        html += "</table>"
       
        # Repeat pagination links at bottom
        if total_pages > 1:
            html += "<div style='margin:10px 0;'>"
            if page > 1:
                html += f"<a href='?page={page-1}' style='margin-right:10px;'>Previous</a>"
           
            for p in range(start_page, end_page + 1):
                if p == page:
                    html += f"<strong style='margin:0 5px;'>{p}</strong>"
                else:
                    html += f"<a href='?page={p}' style='margin:0 5px;'>{p}</a>"
           
            if page < total_pages:
                html += f"<a href='?page={page+1}' style='margin-left:10px;'>Next →</a>"
            html += "</div>"
           
    else:
        html += "<p>No normal commits found.</p>"
   
    html += "<p><a href='/ontology-browser'>Back to Browser</a> | <a href='/'>Back to Home</a></p>"
    html += "</body></html>"
    return html

#  Custom Search Interface
@app.route('/sparql-form', methods=['GET'])
def sparql_form():
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/'>Back to Home</a></p><hr>"
    html += "<h2>SPARQL Query Search</h2>"
    html += "<p>Enter your own SELECT, WHERE, and ORDER BY clauses. Use variable names like ?commit, ?branch, ?repo.</p>"
    html += "<p>Ontology namespace: <code>http://gitontologic/knowledgerep/git#</code></p>"
    html += "<h3>Instructions</h3>"
    html += "<ul>"
    html += "<li><strong>SELECT:</strong> Variables to return (e.g., ?user ?commit)</li>"
    html += "<li><strong>WHERE:</strong> Conditions to match (use git: prefix for properties)</li>"
    html += "<li><strong>ORDER BY:</strong> Sort results by a variable (optional)</li>"
    html += "</ul>"
    html += "<p><strong>Example:</strong> Find all commits by a user:<br>"
    html += "SELECT: ?commit ?message | WHERE: ?commit a git:Commit . ?commit git:authoredBy git:username .</p>"
    html += "<hr>"

    # --- Form input ---
    if 'select' not in request.args:
        html += f'''
        <form method="get" action="/sparql-form" style="line-height:1.8;">
            <label><b>SELECT</b></label><br>
            <input type="text" name="select" size="70" placeholder="?commit ?branch ?message"><br><br>

            <label><b>WHERE</b></label><br>
            <textarea name="where" rows="4" cols="80" placeholder="?commit a git:Commit .&#10;?commit git:onBranch ?branch .&#10;?commit git:authoredBy {base_iri}username ."></textarea><br><br>

            <label><b>ORDER BY</b> (optional)</label><br>
            <input type="text" name="orderby" size="40" placeholder="?branch"><br><br>

            <label><b>Subclass (optional)</b></label><br>
            <select name="subclass">
                <option value="">None</option>
                <option value="InitialCommit">InitialCommit</option>
                <option value="MergeCommit">MergeCommit</option>
                <option value="NormalCommit">NormalCommit</option>
                <option value="MainBranch">MainBranch</option>
                <option value="SecondaryBranch">SecondaryBranch</option>
            </select><br><br>

            <input type="submit" value="Run Query">
        </form>
        '''
        html += "</body></html>"
        return html

    # --- build query ---
    select_clause = request.args.get("select", "").strip()
    where_clause  = request.args.get("where", "").strip()
    orderby_clause = request.args.get("orderby", "").strip()
    subclass = request.args.get("subclass", "").strip()

    # add subclass restriction if chosen
    if subclass:
        where_clause += f"\n?s a git:{subclass} ."

    # full SPARQL query
    query = f"""
    PREFIX git: <{base_iri}>
    SELECT {select_clause}
    WHERE {{
        {where_clause}
    }}
    {('ORDER BY ' + orderby_clause) if orderby_clause else ''}
    """

    html += "<h3>Executing Query:</h3>"
    html += f"<pre>{query}</pre><hr>"

    try:
        results = list(g.query(query))
    except Exception as e:
        html += f"<p style='color:red;'><b>Error:</b> {e}</p>"
        html += "<p><a href='/sparql-form'>Try again</a></p></body></html>"
        return html

    # --- show results ---
    if not results:
        html += "<p>No results found.</p>"
    else:
        html += f"<p>Returned {len(results)} results:</p>"
        html += "<table border=1 cellpadding=5 style='border-collapse:collapse;'>"
        # header row
        vars_ = results[0].labels if hasattr(results[0], 'labels') else select_clause.split()
        html += "<tr style='background:#e0e0e0;'>"
        for v in vars_:
            html += f"<th>{v}</th>"
        html += "</tr>"

        # data rows
        for row in results:
            html += "<tr>"
            for cell in row:
                val = str(cell)
                if "#" in val:
                    val = val.split("#")[-1]
                html += f"<td>{val}</td>"
            html += "</tr>"
        html += "</table>"

    html += "<p><a href='/sparql-form'>New Query</a> | <a href='/'>Home</a></p>"
    html += "</body></html>"
    return html

# validation page
@app.route('/validation')
def validation_page():
    """Check for data quality issues in the ontology"""
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/'>Home</a> | <a href='/ontology-browser'>Browser</a></p>"
    html += "<h2>Ontology Data Validation</h2>"
    html += "<p>Checking for data quality issues...</p><hr>"
   
    errors = []
    warnings = []
   
    # check for tags with no relations 
    tag_count = 0
    orphaned_tags = 0
    for tag in onto.Tag.instances():
        tag_count += 1
        has_relationships = False
        
        # check if any commits refernce this tag
        for commit in onto.Commit.instances():
            try:
                tagged_as_values = getattr(commit, 'taggedAs', None)
                if tagged_as_values:
                    # Handle both single values and lists
                    if isinstance(tagged_as_values, list):
                        if tag in tagged_as_values:
                            has_relationships = True
                            break
                    else:
                        if tag == tagged_as_values:
                            has_relationships = True
                            break
            except:
                continue
                
        if not has_relationships:
            orphaned_tags += 1
   
    if orphaned_tags > 0:
        errors.append(f"Found {orphaned_tags} Lone Tags out of {tag_count} total (Tags with no relationships)")
   
    # commits without authors
    commit_count = 0
    commits_no_author = 0
    for commit in onto.Commit.instances():
        commit_count += 1
        if not commit.authoredBy:
            commits_no_author += 1
   
    if commits_no_author > 0:
        errors.append(f"Found {commits_no_author} Commits out of {commit_count} total missing 'authoredBy' property")
   
    # branches with no commits
    branch_count = 0
    branches_no_commits = 0
    for branch in onto.Branch.instances():
        branch_count += 1
        has_commits = False
        # Check if any commit references this branch
        for commit in onto.Commit.instances():
            if commit.onBranch:
                # Handle both single values and lists
                branch_values = commit.onBranch if hasattr(commit.onBranch, '__iter__') and not isinstance(commit.onBranch, str) else [commit.onBranch]
                if branch in branch_values:
                    has_commits = True
                    break
        if not has_commits:
            branches_no_commits += 1
   
    if branches_no_commits > 0:
        warnings.append(f"Found {branches_no_commits} Branches out of {branch_count} total with no commits")
   
    # check for users that havent authored any commits
    user_count = 0
    users_no_commits = 0
    for user in onto.User.instances():
        user_count += 1
        has_commits = False
        # Check if any commit is authored by this user
        for commit in onto.Commit.instances():
            if commit.authoredBy and commit.authoredBy == user:
                has_commits = True
                break
        if not has_commits:
            users_no_commits += 1
   
    if users_no_commits > 0:
        warnings.append(f"Found {users_no_commits} Users out of {user_count} total with no authored commits")
   
    # Check for Files not connected to repositories
    file_count = 0
    files_no_repo = 0
    for file in onto.File.instances():
        file_count += 1
        if not file.fileOfRepo:
            files_no_repo += 1
   
    if files_no_repo > 0:
        errors.append(f"Found {files_no_repo} Files out of {file_count} total not connected to any Repository")
   
    # Display results
    if not errors and not warnings:
        html += "<div style='color:green; background:#e8f5e8; padding:10px; border-radius:5px;'>"
        html += "<h3>No Data Quality Issues Found!</h3>"
        html += "<p>All checks passed. Your ontology data appears to be well-structured.</p>"
        html += "</div>"
    else:
        # Show errors
        if errors:
            html += "<div style='color:red; background:#f9f9f9; padding:10px; border-radius:5px; margin-bottom:10px;'>"
            html += "<h3>Critical Issues Found:</h3>"
            html += "<ul>"
            for error in errors:
                html += f"<li>{error}</li>"
            html += "</ul>"
            html += "</div>"
       
        # Show warnings
        if warnings:
            html += "<div style='color:orange; background:#f9f9f9; padding:10px; border-radius:5px;'>"
            html += "<h3>Warnings:</h3>"
            html += "<ul>"
            for warning in warnings:
                html += f"<li>{warning}</li>"
            html += "</ul>"
            html += "</div>"
   
    # Summary statistics
    html += "<hr><h3>Data Summary</h3>"
    html += "<table border='1' cellpadding='8' style='border-collapse:collapse;'>"
    html += "<tr><th>Class</th><th>Total Individuals</th></tr>"
    html += f"<tr><td>Tag</td><td>{tag_count}</td></tr>"
    html += f"<tr><td>Commit</td><td>{commit_count}</td></tr>"
    html += f"<tr><td>Branch</td><td>{branch_count}</td></tr>"
    html += f"<tr><td>User</td><td>{user_count}</td></tr>"
    html += f"<tr><td>File</td><td>{file_count}</td></tr>"
    html += "</table>"
   
    html += "<hr><p><a href='/'>Back to Home</a> | <a href='/ontology-browser'>Back to Browser</a></p>"
    html += "</body></html>"
    return html

# section for delete, update, create
@app.route('/data-management')
def data_management():
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/'>Back to Home</a></p>"
    html += "<hr>"
    html += "<h1>Knowledge Graph Data Management</h1>"
    html += "<p>Use these tools to add, update, or remove data from your knowledge graph.</p>"
    
    html += "<div>"
    html += "<h2>Add New Data</h2>"
    html += "<p><a href='/add-user'>Add User</a> | "
    html += "<a href='/add-repository'>Add Repository</a> | "
    html += "<a href='/add-commit'>Add Commit</a> | "
    html += "<a href='/add-file'>Add File</a> | "
    html += "<a href='/add-branch'>Add Branch</a></p>"
    html += "</div>"
    
    html += "<div>"
    html += "<h2>Update Existing Data</h2>"
    html += "<p><a href='/update-data'>Update Data via SPARQL</a></p>"
    html += "</div>"
    
    html += "<div>"
    html += "<h2>Remove Data</h2>"
    html += "<p><a href='/delete-data'>Delete Data via SPARQL</a></p>"
    html += "</div>"
    
    html += "<hr>"
    html += "<p><strong>Note:</strong> Restart the webapp to see newly changed data in the browser.</p>"
    
    html += "</body></html>"
    return html

# function to execute spaqrl updates
def execute_sparql_update(sparql_query):
    # runs sparql update and saves the file
    global g, onto, IRIS
    
    try:
        with onto:
            g.update(sparql_query)
        
        # Save changes to file
        g.serialize(destination=owl_path, format='xml')
        return True, "Update executed and saved successfully. Restart the Flask app to see new data in browser."
            
    except Exception as e:
        return False, f"Error executing update: {str(e)}"

# form for adding users
@app.route('/add-user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        
        if not user_id:
            return "Error: User ID is required", 400
            
        # Build SPARQL INSERT query - just create a basic User entity
        sparql_query = f"""
        INSERT {{
            <{base_iri}{user_id}> a <{base_iri}User> .
        }} WHERE {{}}
        """
        
        success, message = execute_sparql_update(sparql_query)
        
        html = "<html><body style='font-family:Arial; padding:20px;'>"
        html += "<p><a href='/data-management'>Back to Data Management</a></p>"
        html += "<hr>"
        
        if success:
            html += f"<h2>User Added Successfully!</h2>"
            html += f"<p><strong>User ID:</strong> {user_id}</p>"
            html += "<p>Note: Additional properties can be added later when creating commits (author/committer login properties).</p>"
        else:
            html += f"<h2>Error Adding User</h2>"
            html += f"<p>{message}</p>"
            
        html += "<p><a href='/add-user'>Add Another User</a></p>"
        html += "</body></html>"
        return html
    
    # GET request - show form
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/data-management'>Back to Data Management</a></p>"
    html += "<hr>"
    html += "<h2>Add New User</h2>"
    html += "<p><em>Users in the Git ontology represent developers who author and commit code.</em></p>"
    html += "<form method='post' style='max-width:500px;'>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>User ID* (required):</strong></label>"
    html += f"<input type='text' name='user_id' placeholder='e.g., john_doe or developer123' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;' required>"
    html += "<small style='color:#666;'>This should match the login used in commits (commit_author_login/commit_committer_login)</small>"
    html += "</div>"
    html += "<input type='submit' value='Add User'>"
    html += "</form>"
    html += "</body></html>"
    return html

# ADD REPOSITORY FORM AND HANDLER
@app.route('/add-repository', methods=['GET', 'POST'])
def add_repository():
    if request.method == 'POST':
        repo_id = request.form.get('repo_id', '').strip()
        repo_name = request.form.get('repo_name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not repo_id:
            return "Error: Repository ID is required", 400
            
        # Build SPARQL INSERT query
        sparql_query = f"""
        INSERT {{
            <{base_iri}{repo_id}> a <{base_iri}Repository> .
        """
        
        if repo_name:
            sparql_query += f"""
            <{base_iri}{repo_id}> <{base_iri}hasName> "{repo_name}" .
            """
            
        if description:
            sparql_query += f"""
            <{base_iri}{repo_id}> <{base_iri}hasDescription> "{description}" .
            """
            
        sparql_query += "} WHERE {}"
        
        success, message = execute_sparql_update(sparql_query)
        
        html = "<html><body style='font-family:Arial; padding:20px;'>"
        html += "<p><a href='/data-management'>Back to Data Management</a></p>"
        html += "<hr>"
        
        if success:
            html += f"<h2>Repository Added Successfully!</h2>"
            html += f"<p><strong>Repository ID:</strong> {repo_id}</p>"
            if repo_name:
                html += f"<p><strong>Name:</strong> {repo_name}</p>"
            if description:
                html += f"<p><strong>Description:</strong> {description}</p>"
        else:
            html += f"<h2>Error Adding Repository</h2>"
            html += f"<p>{message}</p>"
            
        html += "<p><a href='/add-repository'>Add Another Repository</a></p>"
        html += "</body></html>"
        return html
    
    # GET request - show form
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/data-management'>Back to Data Management</a></p>"
    html += "<hr>"
    html += "<h2>Add New Repository</h2>"
    html += "<form method='post' style='max-width:500px;'>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Repository ID* (required):</strong></label>"
    html += "<input type='text' name='repo_id' placeholder='e.g., repo123' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;' required>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Repository Name:</strong></label>"
    html += "<input type='text' name='repo_name' placeholder='e.g., My Awesome Project' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;'>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Description:</strong></label>"
    html += "<textarea name='description' placeholder='Brief description of the repository...' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px; height:80px;'></textarea>"
    html += "</div>"
    html += "<input type='submit' value='Add Repository'>"
    html += "</form>"
    html += "</body></html>"
    return html

# ADD COMMIT FORM AND HANDLER
@app.route('/add-commit', methods=['GET', 'POST'])
def add_commit():
    if request.method == 'POST':
        commit_id = request.form.get('commit_id', '').strip()
        commit_message = request.form.get('commit_message', '').strip()
        author_id = request.form.get('author_id', '').strip()
        commit_date = request.form.get('commit_date', '').strip()
        branch_id = request.form.get('branch_id', '').strip()
        
        if not commit_id:
            return "Error: Commit ID is required", 400
            
        # Build SPARQL INSERT query
        sparql_query = f"""
        INSERT {{
            <{base_iri}{commit_id}> a <{base_iri}Commit> .
        """
        
        if commit_message:
            sparql_query += f"""
            <{base_iri}{commit_id}> <{base_iri}hasCommitMessage> "{commit_message}" .
            """
            
        if author_id:
            sparql_query += f"""
            <{base_iri}{commit_id}> <{base_iri}authoredBy> <{base_iri}{author_id}> .
            """
            
        if commit_date:
            sparql_query += f"""
            <{base_iri}{commit_id}> <{base_iri}hasCommitDate> "{commit_date}" .
            """
            
        if branch_id:
            sparql_query += f"""
            <{base_iri}{commit_id}> <{base_iri}onBranch> <{base_iri}{branch_id}> .
            """
            
        sparql_query += "} WHERE {}"
        
        success, message = execute_sparql_update(sparql_query)
        
        html = "<html><body style='font-family:Arial; padding:20px;'>"
        html += "<p><a href='/data-management'>Back to Data Management</a></p>"
        html += "<hr>"
        
        if success:
            html += f"<h2>Commit Added Successfully!</h2>"
            html += f"<p><strong>Commit ID:</strong> {commit_id}</p>"
            if commit_message:
                html += f"<p><strong>Message:</strong> {commit_message}</p>"
            if author_id:
                html += f"<p><strong>Author:</strong> {author_id}</p>"
        else:
            html += f"<h2>Error Adding Commit</h2>"
            html += f"<p>{message}</p>"
            
        html += "<p><a href='/add-commit'>Add Another Commit</a></p>"
        html += "</body></html>"
        return html
    
    # GET request - show form
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/data-management'>Back to Data Management</a></p>"
    html += "<hr>"
    html += "<h2>Add New Commit</h2>"
    html += "<form method='post' style='max-width:500px;'>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Commit ID* (required):</strong></label>"
    html += "<input type='text' name='commit_id' placeholder='e.g., commit123' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;' required>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Commit Message:</strong></label>"
    html += "<textarea name='commit_message' placeholder='Brief description of the commit...' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px; height:80px;'></textarea>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Author ID:</strong></label>"
    html += "<input type='text' name='author_id' placeholder='e.g., user123' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;'>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Commit Date:</strong></label>"
    html += "<input type='date' name='commit_date' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;'>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Branch ID:</strong></label>"
    html += "<input type='text' name='branch_id' placeholder='e.g., branch123' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;'>"
    html += "</div>"
    html += "<input type='submit' value='Add Commit'>"
    html += "</form>"
    html += "</body></html>"
    return html

# ADD FILE FORM AND HANDLER
@app.route('/add-file', methods=['GET', 'POST'])
def add_file():
    if request.method == 'POST':
        file_id = request.form.get('file_id', '').strip()
        file_name = request.form.get('file_name', '').strip()
        file_extension = request.form.get('file_extension', '').strip()
        repo_id = request.form.get('repo_id', '').strip()
        
        if not file_id:
            return "Error: File ID is required", 400
            
        # Build SPARQL INSERT query
        sparql_query = f"""
        INSERT {{
            <{base_iri}{file_id}> a <{base_iri}File> .
        """
        
        if file_name:
            sparql_query += f"""
            <{base_iri}{file_id}> <{base_iri}hasFileName> "{file_name}" .
            """
            
        if file_extension:
            sparql_query += f"""
            <{base_iri}{file_id}> <{base_iri}hasFileExtension> "{file_extension}" .
            """
            
        if repo_id:
            sparql_query += f"""
            <{base_iri}{file_id}> <{base_iri}fileOfRepo> <{base_iri}{repo_id}> .
            """
            
        sparql_query += "} WHERE {}"
        
        success, message = execute_sparql_update(sparql_query)
        
        html = "<html><body style='font-family:Arial; padding:20px;'>"
        html += "<p><a href='/data-management'>Back to Data Management</a></p>"
        html += "<hr>"
        
        if success:
            html += f"<h2>File Added Successfully!</h2>"
            html += f"<p><strong>File ID:</strong> {file_id}</p>"
            if file_name:
                html += f"<p><strong>Name:</strong> {file_name}</p>"
            if repo_id:
                html += f"<p><strong>Repository:</strong> {repo_id}</p>"
        else:
            html += f"<h2>Error Adding File</h2>"
            html += f"<p>{message}</p>"
            
        html += "<p><a href='/add-file'>Add Another File</a></p>"
        html += "</body></html>"
        return html
    
    # GET request - show form
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/data-management'>Back to Data Management</a></p>"
    html += "<hr>"
    html += "<h2>Add New File</h2>"
    html += "<form method='post' style='max-width:500px;'>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>File ID* (required):</strong></label>"
    html += "<input type='text' name='file_id' placeholder='e.g., file123' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;' required>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>File Name:</strong></label>"
    html += "<input type='text' name='file_name' placeholder='e.g., main.py' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;'>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>File Extension:</strong></label>"
    html += "<input type='text' name='file_extension' placeholder='e.g., py' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;'>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Repository ID:</strong></label>"
    html += "<input type='text' name='repo_id' placeholder='e.g., repo123' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;'>"
    html += "</div>"
    html += "<input type='submit' value='Add File'>"
    html += "</form>"
    html += "</body></html>"
    return html

# ADD BRANCH FORM AND HANDLER
@app.route('/add-branch', methods=['GET', 'POST'])
def add_branch():
    if request.method == 'POST':
        branch_id = request.form.get('branch_id', '').strip()
        branch_name = request.form.get('branch_name', '').strip()
        repo_id = request.form.get('repo_id', '').strip()
        is_main = request.form.get('is_main') == 'on'
        
        if not branch_id:
            return "Error: Branch ID is required", 400
            
        # Build SPARQL INSERT query
        branch_type = "MainBranch" if is_main else "Branch"
        sparql_query = f"""
        INSERT {{
            <{base_iri}{branch_id}> a <{base_iri}{branch_type}> .
        """
        
        if branch_name:
            sparql_query += f"""
            <{base_iri}{branch_id}> <{base_iri}hasBranchName> "{branch_name}" .
            """
            
        if repo_id:
            sparql_query += f"""
            <{base_iri}{branch_id}> <{base_iri}belongsToRepo> <{base_iri}{repo_id}> .
            """
            
        sparql_query += "} WHERE {}"
        
        success, message = execute_sparql_update(sparql_query)
        
        html = "<html><body style='font-family:Arial; padding:20px;'>"
        html += "<p><a href='/data-management'>Back to Data Management</a></p>"
        html += "<hr>"
        
        if success:
            html += f"<h2>Branch Added Successfully!</h2>"
            html += f"<p><strong>Branch ID:</strong> {branch_id}</p>"
            html += f"<p><strong>Type:</strong> {branch_type}</p>"
            if branch_name:
                html += f"<p><strong>Name:</strong> {branch_name}</p>"
            if repo_id:
                html += f"<p><strong>Repository:</strong> {repo_id}</p>"
        else:
            html += f"<h2>Error Adding Branch</h2>"
            html += f"<p>{message}</p>"
            
        html += "<p><a href='/add-branch'>Add Another Branch</a></p>"
        html += "</body></html>"
        return html
    
    # GET request - show form
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/data-management'>Back to Data Management</a></p>"
    html += "<hr>"
    html += "<h2>Add New Branch</h2>"
    html += "<form method='post' style='max-width:500px;'>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Branch ID* (required):</strong></label>"
    html += "<input type='text' name='branch_id' placeholder='e.g., branch123' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;' required>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Branch Name:</strong></label>"
    html += "<input type='text' name='branch_name' placeholder='e.g., feature/new-feature' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;'>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Repository ID:</strong></label>"
    html += "<input type='text' name='repo_id' placeholder='e.g., repo123' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;'>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:inline-block; margin-bottom:5px;'>"
    html += "<input type='checkbox' name='is_main' style='margin-right:5px;'>"
    html += "<strong>Is Main Branch</strong></label>"
    html += "</div>"
    html += "<input type='submit' value='Add Branch'>"
    html += "</form>"
    html += "</body></html>"
    return html

# UPDATE DATA VIA SPARQL
@app.route('/update-data', methods=['GET', 'POST'])
def update_data():
    if request.method == 'POST':
        entity_uri = request.form.get('entity_uri', '').strip()
        property_uri = request.form.get('property_uri', '').strip()
        old_value = request.form.get('old_value', '').strip()
        new_value = request.form.get('new_value', '').strip()
        
        if not all([entity_uri, property_uri, new_value]):
            return "Error: Entity URI, Property URI, and New Value are required", 400
        
        # Build SPARQL DELETE/INSERT query
        if old_value:
            sparql_query = f"""
            DELETE {{
                <{entity_uri}> <{property_uri}> "{old_value}" .
            }}
            INSERT {{
                <{entity_uri}> <{property_uri}> "{new_value}" .
            }}
            WHERE {{
                <{entity_uri}> <{property_uri}> "{old_value}" .
            }}
            """
        else:
            # If no old value specified, just insert new value
            sparql_query = f"""
            INSERT {{
                <{entity_uri}> <{property_uri}> "{new_value}" .
            }}
            WHERE {{}}
            """
        
        success, message = execute_sparql_update(sparql_query)
        
        html = "<html><body style='font-family:Arial; padding:20px;'>"
        html += "<p><a href='/data-management'>Back to Data Management</a></p>"
        html += "<hr>"
        
        if success:
            html += f"<h2>Data Updated Successfully!</h2>"
            html += f"<p><strong>Entity:</strong> {entity_uri}</p>"
            html += f"<p><strong>Property:</strong> {property_uri}</p>"
            html += f"<p><strong>New Value:</strong> {new_value}</p>"
        else:
            html += f"<h2>Error Updating Data</h2>"
            html += f"<p>{message}</p>"
            
        html += "<p><a href='/update-data'>Update More Data</a></p>"
        html += "</body></html>"
        return html
    
    # GET request - show form
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/data-management'>Back to Data Management</a></p>"
    html += "<hr>"
    html += "<h2>Update Existing Data</h2>"
    html += "<p><em>Update properties of existing entities in your knowledge graph.</em></p>"
    html += "<h3>Instructions</h3>"
    html += "<ul>"
    html += "<li><strong>Entity URI:</strong> Complete URI of the entity to update. Add the entity name after the pre-filled base IRI.</li>"
    html += "<li><strong>Property URI:</strong> The property to update. Add the property name after the pre-filled base IRI.</li>"
    html += "<li><strong>Old Value:</strong> Current value to replace. Leave empty to just add the new value.</li>"
    html += "<li><strong>New Value:</strong> The new value to set for the property.</li>"
    html += "</ul>"
    html += f"<p><strong>Example:</strong> To change a user's name from 'John' to 'Johnny':<br>"
    html += f"Entity URI: {base_iri}user123 | Property URI: {base_iri}hasName | Old Value: John | New Value: Johnny</p>"
    html += "<form method='post' style='max-width:600px;'>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Entity URI* (required):</strong></label>"
    html += f"<input type='text' name='entity_uri' value='{base_iri}' placeholder='e.g., {base_iri}user123' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;' required>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Property URI* (required):</strong></label>"
    html += f"<input type='text' name='property_uri' value='{base_iri}' placeholder='e.g., {base_iri}hasName' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;' required>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Old Value (leave empty to just add new value):</strong></label>"
    html += "<input type='text' name='old_value' placeholder='Current value to replace' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;'>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>New Value* (required):</strong></label>"
    html += "<input type='text' name='new_value' placeholder='New value to set' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;' required>"
    html += "</div>"
    html += "<input type='submit' value='Update Data'>"
    html += "</form>"
    html += "</body></html>"
    return html

# DELETE DATA VIA SPARQL
@app.route('/delete-data', methods=['GET', 'POST'])
def delete_data():
    if request.method == 'POST':
        entity_uri = request.form.get('entity_uri', '').strip()
        property_uri = request.form.get('property_uri', '').strip()
        value = request.form.get('value', '').strip()
        delete_all = request.form.get('delete_all') == 'on'
        
        if not entity_uri:
            return "Error: Entity URI is required", 400
        
        # Build SPARQL DELETE query
        if delete_all:
            # Delete all triples for this entity
            sparql_query = f"""
            DELETE {{
                <{entity_uri}> ?p ?o .
            }}
            WHERE {{
                <{entity_uri}> ?p ?o .
            }}
            """
        elif property_uri and value:
            # Delete specific property-value pair
            sparql_query = f"""
            DELETE {{
                <{entity_uri}> <{property_uri}> "{value}" .
            }}
            WHERE {{
                <{entity_uri}> <{property_uri}> "{value}" .
            }}
            """
        elif property_uri:
            # Delete all values for this property
            sparql_query = f"""
            DELETE {{
                <{entity_uri}> <{property_uri}> ?o .
            }}
            WHERE {{
                <{entity_uri}> <{property_uri}> ?o .
            }}
            """
        else:
            return "Error: Must specify property or check 'delete all'", 400
        
        success, message = execute_sparql_update(sparql_query)
        
        html = "<html><body style='font-family:Arial; padding:20px;'>"
        html += "<p><a href='/data-management'>Back to Data Management</a></p>"
        html += "<hr>"
        
        if success:
            html += f"<h2>Data Deleted Successfully!</h2>"
            html += f"<p><strong>Entity:</strong> {entity_uri}</p>"
            if delete_all:
                html += "<p>All properties and values for this entity were removed.</p>"
            elif property_uri:
                html += f"<p><strong>Property:</strong> {property_uri}</p>"
                if value:
                    html += f"<p><strong>Value:</strong> {value}</p>"
        else:
            html += f"<h2>Error Deleting Data</h2>"
            html += f"<p>{message}</p>"
            
        html += "<p><a href='/delete-data'>Delete More Data</a></p>"
        html += "</body></html>"
        return html
    
    # GET request - show form
    html = "<html><body style='font-family:Arial; padding:20px;'>"
    html += "<p><a href='/data-management'>Back to Data Management</a></p>"
    html += "<hr>"
    html += "<h2>Delete Data</h2>"
    html += "<p><em>Warning: Deletion operations cannot be undone. Use with caution.</em></p>"
    html += "<h3>Instructions</h3>"
    html += "<ul>"
    html += "<li><strong>Entity URI:</strong> Complete URI of the entity to delete. Add the entity name after the pre-filled base IRI.</li>"
    html += "<li><strong>Property URI:</strong> Specific property to delete. Leave empty to delete all properties.</li>"
    html += "<li><strong>Value:</strong> Specific value to delete for the property. Leave empty to delete all values.</li>"
    html += "<li><strong>Delete All Checkbox:</strong> Check this to delete the entire entity and all its data.</li>"
    html += "</ul>"
    html += f"<p><strong>Examples:</strong><br>"
    html += f"Delete entire user: Entity URI: {base_iri}user123 | Check 'Delete All'<br>"
    html += f"Delete specific property: Entity URI: {base_iri}user123 | Property URI: {base_iri}hasName</p>"
    html += "<form method='post' style='max-width:600px;'>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Entity URI* (required):</strong></label>"
    html += f"<input type='text' name='entity_uri' value='{base_iri}' placeholder='e.g., {base_iri}entityname' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;' required>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Property URI (optional):</strong></label>"
    html += f"<input type='text' name='property_uri' value='{base_iri}' placeholder='e.g., {base_iri}hasName' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;'>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:block; margin-bottom:5px;'><strong>Value (optional):</strong></label>"
    html += "<input type='text' name='value' placeholder='Specific value to delete' style='width:100%; padding:8px; border:1px solid #ccc; border-radius:4px;'>"
    html += "</div>"
    html += "<div style='margin:10px 0;'>"
    html += "<label style='display:inline-block; margin-bottom:5px;'>"
    html += "<input type='checkbox' name='delete_all' style='margin-right:5px;'>"
    html += "<strong>Delete ALL data for this entity</strong></label>"
    html += "</div>"
    html += "<input type='submit' value='Delete Data'>"
    html += "</form>"
    html += "</body></html>"
    return html

if __name__ == "__main__":
    app.run(debug=True)