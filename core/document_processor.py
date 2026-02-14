"""
Legal Document Processor - Handles chunking and processing of legal documents
"""

import os
import re
from typing import List, Dict, Any
from pathlib import Path
import hashlib
from core.file_reader import FileReader

class DocumentProcessor:

    def __init__(self, vector_engine):
        self.vector_engine = vector_engine
        self.docs_path = Path(__file__).parent.parent / "legal-docs"
        
        # Chunking parameters optimized for legal documents
        self.chunk_size = 1000  # Slightly larger for legal clauses
        self.chunk_overlap = 150  # More overlap to preserve context
        
        # Legal document categories
        self.categories = {
            'contracts': 'Purchase and Sale Contracts',
            'deeds': 'Property Deeds and Titles',
            'leases': 'Lease Agreements',
            'regulations': 'Property Laws and Regulations'
        }
    
    def process_all_documents(self) -> Dict[str, int]:
        """Process all legal documents in the legal-docs folder"""

        processed_count = 0
        chunk_count = 0

        file_reader = FileReader()

        # Clear existing data
        print("[DocumentProcessor] Clearing existing database...")
        self.vector_engine.clear_collection()

        # Ensure docs folder exists
        if not self.docs_path.exists():
            print(f"[DocumentProcessor] Creating {self.docs_path}")
            self.docs_path.mkdir(parents=True, exist_ok=True)
        
            # Create category subdirectories
            for category in self.categories.keys():
                category_path = self.docs_path / category
                category_path.mkdir(exist_ok=True)
                
                # Create sample document
                self._create_sample_document(category_path, category)
            
            print("[DocumentProcessor] Sample documents created")

        # Process each category
        for category in self.docs_path.iterdir():
            if not category.is_dir():
                continue

            category_name = category.name
            print(f"\n[DocumentProcessor] Processing category: {category_name}")

            for doc_file in category.iterdir():
                if not doc_file.is_file():
                    continue

                try:
                    text = file_reader.read(doc_file)

                    if not text or not text.strip():
                        print(f"  ⚠ Skipping empty file: {doc_file.name}")
                        continue

                    chunks = self.process_document(
                        file_path=doc_file,
                        category=category_name,
                        content=text
                    )

                    chunk_count += len(chunks)
                    processed_count += 1

                    print(f"  ✓ {doc_file.name} ({len(chunks)} chunks)")

                except Exception as e:
                    print(f"  ✗ Error processing {doc_file.name}: {e}")

        return {
            "processed": processed_count,
            "chunks": chunk_count
        }

    
    def process_document(self,file_path: Path,category: str,content: str) -> List[Dict[str, Any]]:
        
        """Process a single legal document into chunks"""

        # Extract metadata
        title = self._extract_title(content)
        doc_type = self._identify_document_type(content, file_path.name)
        doc_id = hashlib.md5(str(file_path).encode()).hexdigest()

        # Create legal-aware chunks
        chunks = self._create_legal_chunks(content)

        processed_chunks = []

        for i, chunk_text in enumerate(chunks):
            chunk_data = {
                "id": f"{doc_id}_{i}",
                "text": chunk_text,
                "metadata": {
                    "title": title or file_path.stem.replace('-', ' ').replace('_', ' ').title(),
                    "category": category,
                    "document_type": doc_type,
                    "file": file_path.name,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            }

            # Add to vector store
            self.vector_engine.add_document(
                chunk_data["id"],
                chunk_text,
                chunk_data["metadata"]
            )

            processed_chunks.append(chunk_data)

        return processed_chunks
    
    def list_available_documents(self) -> List[Dict[str, Any]]:
        """List all available legal documents"""
        documents = []
        
        if not self.docs_path.exists():
            return documents
        
        for category in self.docs_path.iterdir():
            if category.is_dir():
                for doc_file in category.glob("*.md"):
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    title = self._extract_title(content)
                    
                    documents.append({
                        'title': title or doc_file.stem.replace('-', ' ').title(),
                        'category': category.name,
                        'filename': doc_file.name,
                        'size': doc_file.stat().st_size
                    })
        
        return documents
    
    def _extract_title(self, content: str) -> str:
        """Extract title from markdown document"""
        # Look for # Title format
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1)
        
        # Look for title in first line
        lines = content.split('\n')
        if lines:
            first_line = lines[0].strip()
            if first_line and not first_line.startswith('#'):
                return first_line[:100]
        
        return None
    
    def _identify_document_type(self, content: str, filename: str) -> str:
        """Identify the type of legal document"""
        content_lower = content.lower()
        
        if 'lease' in content_lower or 'tenant' in content_lower or 'rent' in content_lower:
            return 'Lease Agreement'
        elif 'deed' in content_lower or 'title' in content_lower or 'grantor' in content_lower:
            return 'Property Deed'
        elif 'purchase' in content_lower or 'sale' in content_lower or 'buyer' in content_lower:
            return 'Purchase Contract'
        elif 'regulation' in content_lower or 'zoning' in content_lower or 'ordinance' in content_lower:
            return 'Regulation'
        else:
            return 'Legal Document'
    
    def _create_legal_chunks(self, text: str) -> List[str]:
        """Create chunks optimized for legal documents"""
        chunks = []
        
        # Try to split by sections first (legal documents often have numbered sections)
        sections = self._split_by_sections(text)
        
        if len(sections) > 1:
            # Process each section
            for section in sections:
                if len(section) <= self.chunk_size:
                    chunks.append(section.strip())
                else:
                    # Section too large, split further
                    sub_chunks = self._create_chunks(section)
                    chunks.extend(sub_chunks)
        else:
            # No clear sections, use standard chunking
            chunks = self._create_chunks(text)
        
        return [c for c in chunks if c.strip()]
    
    def _split_by_sections(self, text: str) -> List[str]:
        """Split legal document by numbered sections or articles"""
        # Pattern for common legal section markers
        patterns = [
            r'\n\s*(?:Section|SECTION|Article|ARTICLE)\s+\d+',
            r'\n\s*\d+\.\s+[A-Z]',  # 1. SECTION NAME
            r'\n\s*[A-Z]\.\s+[A-Z]'  # A. SECTION NAME
        ]
        
        for pattern in patterns:
            sections = re.split(pattern, text)
            if len(sections) > 1:
                # Reconstruct sections with their headers
                result = []
                matches = re.finditer(pattern, text)
                match_list = list(matches)
                
                if match_list:
                    # Add content before first section
                    if sections[0].strip():
                        result.append(sections[0])
                    
                    # Add sections with headers
                    for i, match in enumerate(match_list):
                        section_content = match.group() + (sections[i + 1] if i + 1 < len(sections) else '')
                        result.append(section_content)
                    
                    return result
        
        return [text]
    
    def _create_chunks(self, text: str) -> List[str]:
        """Create overlapping chunks from text"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to find a good break point
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind('\n\n', start, end)
                if para_break > start + self.chunk_size // 2:
                    end = para_break
                else:
                    # Look for sentence end
                    sentence_end = text.rfind('. ', start, end)
                    if sentence_end > start + self.chunk_size // 2:
                        end = sentence_end + 1
                    else:
                        # Look for any period
                        period = text.rfind('.', start, end)
                        if period > start + self.chunk_size // 2:
                            end = period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
        
        return chunks
    
    def _create_sample_document(self, category_path: Path, category: str):
        """Create a sample legal document for demonstration"""
        
        samples = {
            'contracts': {
                'filename': 'sample-purchase-agreement.md',
                'content': '''# Property Purchase Agreement

## Purchase and Sale Agreement

**Date:** January 15, 2024

**PARTIES:**
- **Buyer:** John Smith, 123 Main Street, Cityville, ST 12345
- **Seller:** Jane Doe, 456 Oak Avenue, Townsburg, ST 67890

**PROPERTY DESCRIPTION:**
The property located at 789 Elm Street, Cityville, ST 12345, legally described as Lot 15, Block 3, Greenwood Subdivision, including all improvements and fixtures.

## SECTION 1: PURCHASE PRICE

The total purchase price is **$450,000** (Four Hundred Fifty Thousand Dollars), payable as follows:
- Earnest money deposit: $10,000 (due upon signing)
- Down payment: $90,000 (due at closing)
- Mortgage financing: $350,000

## SECTION 2: CLOSING DATE

The closing shall occur on or before March 1, 2024, at a location mutually agreed upon by both parties.

## SECTION 3: TITLE AND INSPECTION

3.1 **Title Insurance:** Seller shall provide clear and marketable title, free from all liens and encumbrances.

3.2 **Property Inspection:** Buyer has the right to conduct inspections within 15 days of this agreement. If material defects are found, Buyer may:
   - Request repairs
   - Renegotiate purchase price
   - Terminate this agreement

3.3 **Survey:** Seller shall provide a current property survey at Seller's expense.

## SECTION 4: CONTINGENCIES

This agreement is contingent upon:
- Buyer obtaining mortgage financing at an interest rate not exceeding 7%
- Property appraisal at or above purchase price
- Satisfactory home inspection
- Clear title search

## SECTION 5: SELLER REPRESENTATIONS

Seller represents and warrants that:
- All systems (HVAC, plumbing, electrical) are in working order
- There are no known material defects
- No pending litigation affects the property
- All required permits for improvements have been obtained

## SECTION 6: DEFAULT AND REMEDIES

If Buyer defaults, Seller may retain the earnest money as liquidated damages. If Seller defaults, Buyer may seek specific performance or damages.

## SECTION 7: CLOSING COSTS

Buyer shall pay: Loan origination fees, appraisal, credit report, and title insurance.
Seller shall pay: Real estate commissions, deed preparation, and property transfer taxes.

**SIGNATURES:**

_________________________          _________________________
John Smith (Buyer)                 Jane Doe (Seller)

Date: _______________              Date: _______________
'''
            },
            'deeds': {
                'filename': 'sample-warranty-deed.md',
                'content': '''# Warranty Deed

## GENERAL WARRANTY DEED

**STATE OF [STATE]**
**COUNTY OF [COUNTY]**

**Grantor:** Robert Johnson and Mary Johnson, husband and wife
**Grantor's Address:** 321 Pine Street, Cityville, ST 12345

**Grantee:** Thomas Williams and Sarah Williams, husband and wife
**Grantee's Address:** 654 Maple Drive, Cityville, ST 12345

**Consideration:** The sum of Ten Dollars ($10.00) and other good and valuable consideration

## PROPERTY DESCRIPTION

The Grantor, for the consideration above, hereby conveys and warrants to the Grantee the following real property:

**Legal Description:**
Lot 22, Block 7, Riverside Heights Subdivision, according to the plat recorded in Plat Book 45, Page 89, Records of [County] County, [State].

**Common Address:** 987 River Road, Cityville, ST 12345

## COVENANTS AND WARRANTIES

The Grantor hereby covenants with the Grantee:

1. **Covenant of Seisin:** Grantor is lawfully seized of the property and has the right to convey it.

2. **Covenant Against Encumbrances:** The property is free from all encumbrances except:
   - Current year property taxes (prorated)
   - Utility easements of record
   - Recorded subdivision restrictions

3. **Covenant of Quiet Enjoyment:** Grantee shall quietly enjoy the property without lawful claims by others.

4. **Covenant of Warranty:** Grantor will warrant and defend the title against all lawful claims.

5. **Covenant of Further Assurances:** Grantor will execute any additional documents necessary to perfect title.

## APPURTENANT RIGHTS

This conveyance includes all rights, privileges, and appurtenances, including:
- Water rights
- Mineral rights (surface only)
- Easements and access rights

## HOMESTEAD WAIVER

The undersigned spouse joins in this conveyance to waive any homestead rights in the property.

**EXECUTED** this _____ day of _____________, 2024.

**GRANTOR:**

_________________________          _________________________
Robert Johnson                     Mary Johnson


**STATE OF [STATE]**
**COUNTY OF [COUNTY]**

On this _____ day of _____________, 2024, before me appeared Robert Johnson and Mary Johnson, known to me to be the persons described in and who executed the foregoing instrument.

_________________________
Notary Public

My Commission Expires: _____________
'''
            },
            'leases': {
                'filename': 'sample-residential-lease.md',
                'content': '''# Residential Lease Agreement

## RESIDENTIAL RENTAL AGREEMENT

**Effective Date:** February 1, 2024

**LANDLORD:**
Premium Properties LLC
Contact: James Anderson
Address: 100 Business Park, Cityville, ST 12345
Phone: (555) 123-4567

**TENANT:**
Emily Rodriguez
Phone: (555) 987-6543
Email: emily.rodriguez@email.com

**PROPERTY ADDRESS:**
Apartment 2B, 555 Garden Street, Cityville, ST 12345

## SECTION 1: LEASE TERM

This lease begins on **February 1, 2024** and ends on **January 31, 2025** (12-month term).

## SECTION 2: RENT

2.1 **Monthly Rent:** $1,800 per month, due on the 1st of each month.

2.2 **Late Fees:** Rent not received by the 5th will incur a $75 late fee, plus $10 per day thereafter.

2.3 **Payment Method:** Payments accepted via check, money order, or electronic transfer to account [XXXXX].

2.4 **Security Deposit:** $1,800 (one month's rent) due at lease signing.

## SECTION 3: UTILITIES AND SERVICES

**Tenant Responsible For:**
- Electricity
- Gas
- Internet/Cable
- Renter's insurance (required)

**Landlord Responsible For:**
- Water and sewer
- Trash collection
- Common area maintenance
- Property insurance

## SECTION 4: OCCUPANCY

Maximum occupancy: Two (2) persons. No additional occupants without written landlord consent.

## SECTION 5: PETS

5.1 **Pet Policy:** One pet permitted with additional $500 refundable pet deposit and $50/month pet rent.

5.2 **Restrictions:**
- Maximum weight: 40 pounds
- Prohibited breeds: [List specific breeds]
- Must be licensed and vaccinated
- No aggressive behavior

## SECTION 6: MAINTENANCE AND REPAIRS

6.1 **Tenant Duties:**
- Keep premises clean and sanitary
- Dispose of trash properly
- Replace light bulbs and batteries
- Report maintenance issues within 24 hours
- Maintain HVAC filters monthly

6.2 **Landlord Duties:**
- Maintain structural integrity
- Repair major systems (HVAC, plumbing, electrical)
- Ensure habitability standards
- Respond to emergency repairs within 24 hours

## SECTION 7: ALTERATIONS

No alterations, painting, or improvements without written landlord consent. Any approved alterations become property of landlord.

## SECTION 8: SUBLETTING

Subletting or assignment prohibited without written landlord consent.

## SECTION 9: ENTRY AND INSPECTION

Landlord may enter with 24-hour notice for:
- Inspections
- Repairs
- Showings to prospective tenants (last 60 days of lease)

Emergency entry permitted without notice.

## SECTION 10: TERMINATION

10.1 **Early Termination:** Tenant may terminate early with 60-day notice and payment of two months' rent as early termination fee.

10.2 **Holdover:** Continued occupancy after lease end creates month-to-month tenancy at 125% of monthly rent.

10.3 **Eviction:** Non-payment of rent or violation of terms may result in eviction proceedings.

## SECTION 11: SECURITY DEPOSIT RETURN

Deposit returned within 30 days of move-out, less deductions for:
- Unpaid rent
- Damages beyond normal wear and tear
- Cleaning fees
- Unpaid utilities

Detailed itemization provided with any deductions.

## SECTION 12: TENANT OBLIGATIONS

- Comply with all building rules and regulations
- Maintain quiet enjoyment for neighbors
- No illegal activities
- Obtain renter's insurance ($100,000 minimum liability)
- No smoking inside the unit

**SIGNATURES:**

_________________________          _________________________
Emily Rodriguez (Tenant)           James Anderson (Landlord)
Date: _______________              Date: _______________
'''
            },
            'regulations': {
                'filename': 'zoning-and-property-regulations.md',
                'content': '''# Property Zoning and Regulations Guide

## City of Cityville Property Regulations

**Effective Date:** January 1, 2024
**Authority:** City Council Ordinance #2024-001

## SECTION 1: RESIDENTIAL ZONING CLASSIFICATIONS

### R-1 Single Family Residential

**Permitted Uses:**
- Single-family detached homes
- Home offices (no exterior signage)
- Accessory dwelling units (ADUs) subject to restrictions

**Lot Requirements:**
- Minimum lot size: 7,500 sq ft
- Minimum frontage: 75 feet
- Maximum lot coverage: 35%

**Setbacks:**
- Front: 25 feet
- Side: 10 feet
- Rear: 20 feet

**Height Limits:** 35 feet (2.5 stories maximum)

### R-2 Multi-Family Residential

**Permitted Uses:**
- Duplexes
- Townhomes
- Apartments (up to 4 units)

**Density:** Maximum 12 units per acre

**Parking:** 2 spaces per unit required

## SECTION 2: BUILDING PERMITS

### When Permits Required:

**Always Required:**
- New construction
- Additions over 100 sq ft
- Structural modifications
- Electrical system changes
- Plumbing installations
- HVAC system replacement
- Deck construction over 30" high

**Permit Exempt:**
- Painting and wallpaper
- Floor covering installation
- Minor repairs
- Fences under 6 feet (residential)
- Playground equipment

### Application Process:

1. Submit completed application with:
   - Site plan
   - Building plans
   - Engineering documents (if required)
   - Fee payment

2. Review period: 10-15 business days

3. Inspections required at:
   - Foundation stage
   - Framing stage
   - Final completion

## SECTION 3: PROPERTY MAINTENANCE STANDARDS

### Required Maintenance:

**Exterior:**
- Paint maintained without peeling/chipping
- Siding/brick in good repair
- Roof weather-tight and sound
- Gutters and downspouts functional
- Windows intact without cracks

**Yard:**
- Grass cut below 8 inches
- Weeds controlled
- Trees/shrubs trimmed
- No junk or debris storage
- Drainage maintained

**Violations:** Warning issued, 30 days to correct, $100/day penalty thereafter

## SECTION 4: FENCE REGULATIONS

**Height Limits:**
- Front yard: 3 feet maximum
- Side/rear yard: 6 feet maximum
- Corner lots: 3 feet in visibility triangle

**Materials:** Wood, vinyl, metal, or masonry. Chain-link permitted in rear yards only.

**Setbacks:** Must be inside property line, 2 feet from utility easements

**Permit Required:** Yes, for fences over 6 feet

## SECTION 5: ACCESSORY STRUCTURES

### Detached Garages/Sheds:

**Size Limits:**
- Maximum 800 sq ft in R-1 zones
- Maximum 25% of rear yard area
- Maximum height: 15 feet

**Location:**
- Not in front yard
- Minimum 5 feet from property lines
- Minimum 10 feet from primary structure

**Permit Required:** Yes, for structures over 120 sq ft

### Accessory Dwelling Units (ADUs):

**Requirements:**
- Maximum 800 sq ft or 50% of primary dwelling
- Owner must occupy either primary or ADU
- Separate entrance required
- Parking: 1 additional space required
- Must match architectural style

**Special Permit Required:** Yes, plus variance for lots under 10,000 sq ft

## SECTION 6: HOME OCCUPATION REGULATIONS

**Permitted Activities:**
- Professional offices
- Arts and crafts
- Tutoring
- Online businesses

**Restrictions:**
- No exterior signage
- No customer traffic exceeding residential levels
- No exterior storage
- Must be incidental to residential use
- No employees outside household

**Business License Required:** Yes, annual fee $75

## SECTION 7: PARKING REQUIREMENTS

**Residential:**
- Single family: 2 spaces
- Multi-family: 2 spaces per unit
- Guest parking: 0.25 spaces per unit

**Driveway Standards:**
- Minimum width: 10 feet (single), 20 feet (double)
- Maximum width: 40% of lot frontage
- Must be paved material (concrete, asphalt, pavers)

**Street Parking:** No parking on lawn or unpaved surfaces

## SECTION 8: TREE PROTECTION

**Protected Trees:**
- Heritage trees (diameter >24")
- Street trees
- Trees in protected areas

**Removal Permit Required:** For trees >6" diameter

**Replacement:** 1:1 ratio, minimum 2" caliper

**Penalties:** $500 per tree illegally removed

## SECTION 9: PROPERTY LINE DISPUTES

**Survey Requirements:**
- Licensed surveyor
- Monumented boundaries
- Recorded with county

**Resolution Process:**
1. Attempt neighbor agreement
2. Formal survey
3. Mediation
4. Legal action if necessary

## SECTION 10: VARIANCE PROCESS

**When Needed:** Deviation from zoning requirements due to hardship

**Application:**
- Written request with justification
- Site plan showing proposed variance
- Notice to adjacent property owners
- Fee: $500

**Board Review:** Zoning Board of Appeals hearing within 60 days

**Approval Criteria:**
- Unique hardship exists
- Not self-created
- Minimum variance necessary
- No adverse impact on neighborhood

## ENFORCEMENT

**Code Enforcement Officer:** (555) 555-CODE

**Violation Process:**
1. Warning notice (10 days to correct)
2. Citation ($100-$500 per day)
3. Court action if unresolved

**Appeals:** Planning Commission within 30 days

---

**For More Information:**
City Planning Department
100 City Hall Plaza
Cityville, ST 12345
Phone: (555) 555-ZONE
Website: www.cityville.gov/planning
'''
            }
        }
        
        if category in samples:
            sample_file = category_path / samples[category]['filename']
            with open(sample_file, 'w', encoding='utf-8') as f:
                f.write(samples[category]['content'])
            print(f"  Created sample: {samples[category]['filename']}")