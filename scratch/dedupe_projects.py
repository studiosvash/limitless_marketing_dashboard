import os
import sys
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select
from pipeline.db.schema import Site
from pipeline.utils.db_connection import get_session
from pipeline.services.site_service import _bare_domain

def main():
    with get_session() as session:
        sites = session.execute(select(Site)).scalars().all()
        
        domain_map = {}
        for site in sites:
            bare = _bare_domain(site.site_url).lower()
            if bare not in domain_map:
                domain_map[bare] = []
            domain_map[bare].append(site)
            
        deleted_count = 0
        for bare, site_list in domain_map.items():
            if len(site_list) > 1:
                # Sort by id (oldest first)
                site_list.sort(key=lambda x: x.id)
                keep_site = site_list[0]
                delete_sites = site_list[1:]
                
                print(f"Keeping {keep_site.site_url} (ID: {keep_site.id}) for domain {bare}")
                for ds in delete_sites:
                    print(f"Deleting duplicate {ds.site_url} (ID: {ds.id})")
                    session.delete(ds)
                    deleted_count += 1
                    
        if deleted_count > 0:
            session.commit()
            print(f"Deleted {deleted_count} duplicate sites.")
        else:
            print("No duplicates found.")

if __name__ == '__main__':
    main()
