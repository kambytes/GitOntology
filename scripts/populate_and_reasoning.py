# kamleshkumar Senthilkumar - 24245674
# Andoni Karafilakis - 24314657

# Loads the base ontology, populates individuals from JSON metadata, and runs the Pellet reasoner with SWRL rules.
# The ontology has been created using Protogé. 
# The git_ontology_base.owl is the designed schema (classes, properties, axioms and SWRL rules) for our knowledge graph.
# The git_ontology_reasoned.owl is populated and reasoned version with infered triples.  

from owlready2 import *
import owlready2
import os, json, re
from datetime import datetime, timezone

# stop error of heap limit exceeded
owlready2.reasoning.JAVA_MEMORY = 8000   # 8 GB heap

# Load base ontology and create new ontology that imports the base 
# A reasoned .owl file saved after running Pellet
onto_path.append("ontology")

onto = get_ontology("ontology/git_ontology_base.owl").load()
print("Loaded base ontology")

# Save a working copy (so base remains untouched)
onto.save(file="ontology/git_ontology_populated.owl", format="rdfxml")
populated_onto = get_ontology("git_ontology_populated.owl").load()

# Load JSON datasets
with open("data/repos.json") as f: 
    repos_data = json.load(f)
with open("data/branches.json") as f: 
    branches_data = json.load(f)
with open("data/commits.json") as f: 
    commits_data  = json.load(f)
with open("data/files.json") as f: 
    files_data    = json.load(f)
with open("data/users.json") as f: 
    users_data = json.load(f)

print("Metadata loaded successfully")

# Caches
repos, branches, users, commits, files, tags = {}, {}, {}, {}, {}, {}

# for validating and converting types
def safe_int(x):
    try:
        return int(x)
    except Exception:
        return 0

def safe_str(x): 
    return "" if x is None else str(x)

def safe_bool(x):
    if isinstance(x, bool):
        return x
    if isinstance(x, str):
        return x.strip().lower() == "true"
    return bool(x)

def parse_datetime(value):
    if not value: return None
    try:
        val = value.replace("Z","+00:00")
        dt = datetime.fromisoformat(val)
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception: return None

# Add your SWRL rules here.
with onto:
    '''
        SampleRule = Imp()
        SampleRule.set_as_rule("""
            Commit(?c), committedBy(?c, ?u), onBranch(?c, ?b), belongsToRepo(?b, ?r)
            -> contributesTo(?u, ?r)
        """)
    '''   
    pass

# Populate ontology
with populated_onto:

    # (OBJECT) User
    print("Populating users...")
    for u in users_data:
        login = safe_str(u.get("user_login"))
        uid   = safe_int(u.get("user_id"))
        iri   = f"user_{login or uid}"
        user  = populated_onto.User(iri)
        user.user_id = uid
        user.user_login = login
        if hasattr(user, "user_url"):
            user.user_url = safe_str(u.get("user_url"))
        users[login] = user

    # (OBJECT) Repository
    print("Populating repositories...")
    for r in repos_data:
        rid_int = safe_int(r.get("repo_id"))
        rid = str(rid_int) if rid_int else str(len(repos))
        iri = f"repo_{rid}"
        repo = populated_onto.Repository(iri)
        repo.repo_id = rid_int
        repo.repo_name = safe_str(r.get("repo_name"))
        repo.repo_description = safe_str(r.get("repo_description"))
        repo.repo_language = safe_str(r.get("repo_language"))
        repo.repo_forks = safe_int(r.get("repo_forks"))
        repo.repo_stars = safe_int(r.get("repo_stars"))
        repo.repo_url = safe_str(r.get("repo_url"))
        repos[rid_int] = repo

    # (OBJECT) Branch
    print("Populating branches...")
    for b in branches_data:
        bname = safe_str(b.get("branch_name"))
        rid_int = safe_int(b.get("repo_id"))
        key = f"{rid_int}__{bname}"
        iri = re.sub(r"[^a-zA-Z0-9_]", "_", f"branch_{key}")
        branch = populated_onto.Branch(iri)
        branch.branch_name = bname
        is_def = safe_bool(b.get("is_default"))
        if is_def is not None:
            branch.is_default = is_def
        repo = repos.get(rid_int)
        if repo:
            branch.belongsToRepo = repo
        branches[key] = branch

    # (OBJECT) File
    print("Populating files...")
    for fobj in files_data:
        fid = safe_str(fobj.get("file_id", len(files)))
        iri = f"file_{fid}"
        file = populated_onto.File(iri)
        file.file_id = fid
        file.file_name = safe_str(fobj.get("file_name"))
        file.file_status = safe_str(fobj.get("file_status"))
        file.file_additions = safe_int(fobj.get("file_additions"))
        file.file_deletions = safe_int(fobj.get("file_deletions"))
        file.file_changes = safe_int(fobj.get("file_changes"))
        files[fid] = file

        # (OBJECT PROPERTY) fileOfRepo
        rid_int = safe_int(fobj.get("repo_id"))
        repo = repos.get(rid_int)
        if repo and hasattr(file, "fileOfRepo"):
            file.fileOfRepo = repo

    # (OBJECT) Commit
    print("Populating commits...")
    for c in commits_data:
        sha = safe_str(c.get("commit_sha"))
        rid_int = safe_int(c.get("repo_id"))
        # Slightly richer IRI: include repo context
        iri = f"commit_{rid_int}_{sha}"
        commit = populated_onto.Commit(iri)
        commit.commit_sha = sha
        commit.commit_message = safe_str(c.get("commit_message"))
        dt = parse_datetime(c.get("commit_date"))
        if dt: commit.commit_date = dt
        commit.commit_parent_count = safe_int(c.get("commit_parent_count"))
        is_init = safe_bool(c.get("is_initial"))
        if is_init is not None:
            commit.is_initial = is_init

        # (OBJECT PROPERTY) onBranch
        bname = safe_str(c.get("branch_name"))
        bkey = f"{rid_int}__{bname}"
        branch = branches.get(bkey)
        if branch:
            commit.onBranch = [branch]

        # (OBJECT PROPERTY) committedBy & authoredBy
        author_login = safe_str(c.get("commit_author_login"))
        committer_login = safe_str(c.get("commit_committer_login"))
        if author_login in users:
            commit.authoredBy = users[author_login]
        if committer_login in users:
            commit.committedBy = users[committer_login]

        # (OBJECT PROPERTY) hasCommit
        repo = repos.get(rid_int)
        if repo and hasattr(repo, "hasCommit") and commit not in repo.hasCommit:
            repo.hasCommit.append(commit)

        # (OBJECT PROPERTY) contributesTo & hasContributors
        if repo and author_login in users:
            user = users[author_login]
            if hasattr(user, "contributesTo") and repo not in user.contributesTo:
                user.contributesTo.append(repo)
            if hasattr(repo, "hasContributors") and user not in repo.hasContributors:
                repo.hasContributors.append(user)
        if repo and committer_login in users:
            user = users[committer_login]
            if hasattr(user, "contributesTo") and repo not in user.contributesTo:
                user.contributesTo.append(repo)
            if hasattr(repo, "hasContributors") and user not in repo.hasContributors:
                repo.hasContributors.append(user)

        # (OBJECT PROPERTY) taggedAs 
        tag_list = c.get("commit_tags") or []
        if isinstance(tag_list, str):
            tag_list = [t for t in re.split(r"[,\s;]+", tag_list) if t]
        for t in tag_list:
            t_clean = safe_str(t).strip()
            if not t_clean: continue
            tag_iri = re.sub(r"[^a-zA-Z0-9_]", "_", f"tag_{t_clean}")
            tag = tags.get(tag_iri) or populated_onto.Tag(tag_iri)
            tag.tag_name = t_clean
            tags[tag_iri] = tag
            if hasattr(commit, "taggedAs") and tag not in commit.taggedAs:
                commit.taggedAs.append(tag)

        commits[iri] = commit

    # (OBJECT PROPERTY) hasParentCommit
    print("Linking parent commits...")
    for c in commits_data:
        child_sha = safe_str(c.get("commit_sha"))
        rid_int = safe_int(c.get("repo_id"))
        child_iri = f"commit_{rid_int}_{child_sha}"
        child = commits.get(child_iri)
        if not child: continue
        parents_field = c.get("commit_parents")
        parents = []
        if isinstance(parents_field, list):
            parents = [safe_str(p) for p in parents_field if p]
        elif isinstance(parents_field, str):
            parents = [p for p in re.split(r"[,\s;]+", parents_field) if p]
        for psha in parents:
            parent_iri = f"commit_{rid_int}_{psha}"
            parent = commits.get(parent_iri) or populated_onto.Commit(parent_iri)
            parent.commit_sha = psha
            commits[parent_iri] = parent
            if hasattr(child, "hasParentCommit") and parent not in child.hasParentCommit:
                child.hasParentCommit.append(parent)

# Save populated ontology
populated_onto.save(file="ontology/git_ontology_populated.owl", format="rdfxml")
print("Saved populated ontology.")

# Run reasoner (Pellet) to apply SWRL rules and classify
print("Running Pellet reasoner with SWRL rules. Please Allow 1-3 Minutes")
try:
    sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=True, debug=2)
    print("Reasoning complete. Ontology consistent.")
except OwlReadyInconsistentOntologyError:
    print("Ontology inconsistent.")
except Exception as e:
    print("Reasoner failed:", e)

populated_onto.save(file="ontology/git_ontology_reasoned.owl", format="rdfxml")

print("Saved reasoned ontology.")