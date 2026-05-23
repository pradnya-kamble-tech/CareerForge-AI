import sys
import os
import unittest
import json

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from analyzer import score_resume, extract_skills, load_domain_keywords

class AnalyzerTestCase(unittest.TestCase):
    def setUp(self):
        # Expanded marketing resume to meet word count and keyword coverage
        self.marketing_resume = """
        DIGITAL MARKETING STRATEGIST
        Professional with over 5 years of experience in Digital Marketing, SEO, and SEM.
        Proven track record in Content Strategy and Social Media Management.
        Expertise in Google Analytics, Email Marketing, and Brand Identity development.
        Skilled in Market Research, CRM implementation, and PPC campaign management.
        Proficient in Copywriting and Campaign Management across multiple platforms.
        
        Experience:
        - Launched multiple high-impact digital marketing campaigns.
        - Managed a diverse team of content creators and social media managers.
        - Analyzed market trends to optimize PPC spend and increase ROI.
        - Developed comprehensive SEO strategies that increased organic traffic by 60%.
        - Increased customer engagement through targeted email marketing and CRM segmentation.
        - Spearheaded brand identity refresh across all digital touchpoints.
        - Executed global marketing strategies resulting in 2M+ reach.
        - Promoted new product lines using Influencer Marketing and A/B Testing.
        - Negotiated partnerships to expand market research capabilities.
        - Drafted copy for high-converting landing pages.
        
        Education:
        Bachelor of Science in Marketing, University of Digital Arts.
        Certified Google Analytics Professional.
        
        Skills & Tools:
        Digital Marketing, SEO, SEM, Content Strategy, Social Media Management,
        Google Analytics, Email Marketing, Brand Identity, CRM, PPC, Copywriting,
        Public Relations, Influencer Marketing, A/B Testing, Conversion Rate Optimization,
        Customer Segmentation, Adobe Creative Suite, E-commerce, Sales Funnel.
        """ * 3  # Repeat to ensure length > 200 words
        
        self.engineering_resume = """
        SENIOR SOFTWARE ENGINEER
        Experienced software engineer with 10 years of experience in Python and Java.
        Specialized in System Design, Algorithms, and Data Structures.
        Hands-on experience with Docker, Kubernetes, and AWS cloud infrastructure.
        Developed high-performance REST APIs and Microservices architectures.
        Strong background in CI/CD, Unit Testing, and Agile development.
        
        Achievements:
        - Architected a distributed data processing engine using Kafka and Spark.
        - Engineered a real-time monitoring system that reduced downtime by 40%.
        - Optimized database queries in SQL and NoSQL for higher throughput.
        - Refactored legacy monolithic applications into microservices.
        - Deployed containerized applications using Kubernetes.
        - Implemented automated testing frameworks reducing bug reports by 30%.
        - Integrated various third-party services using RESTful APIs.
        - Debugged complex production issues across the stack.
        - Scaled applications to handle 100k+ concurrent users.
        - Automated infrastructure provisioning using Terraform.
        
        Skills:
        Python, Java, C++, SQL, Git, Docker, Kubernetes, AWS, REST API,
        Microservices, Data Structures, Algorithms, React, Node.js, CI/CD,
        Unit Testing, System Design, NoSQL, Redis, Kafka, TensorFlow, Agile.
        """ * 3 # Repeat to ensure length > 200 words

    def test_marketing_domain_score(self):
        """Test that a marketing resume scores high in the Marketing domain."""
        result = score_resume(self.marketing_resume, domain='Marketing')
        # Marketing resume has many marketing keywords + structure + verbs
        self.assertGreaterEqual(result['score'], 50)
        self.assertEqual(result['level'], 'Advanced' if result['score'] >= 70 else 'Intermediate')

    def test_mismatched_domain_score(self):
        """Test that an engineering resume scores low in the Healthcare domain."""
        result = score_resume(self.engineering_resume, domain='Healthcare')
        # Healthcare critical keywords are things like 'Patient Care', 'HIPAA'
        # Engineering resume has NONE of those.
        # It gets points for structure/length though.
        self.assertLess(result['score'], 50)

    def test_empty_text_score(self):
        """Test that empty text returns a low score and doesn't crash."""
        result = score_resume("", domain='Engineering')
        self.assertEqual(result['score'], 0)

    def test_all_12_domains_load(self):
        """Test that keywords for all 12 domains can be loaded without error."""
        domains = [
            'Engineering', 'Healthcare', 'Finance', 'Marketing', 
            'Design', 'Legal', 'HR', 'Operations', 
            'Education', 'Sales', 'Hospitality', 'Construction'
        ]
        for domain in domains:
            keywords = load_domain_keywords(domain)
            self.assertIn('critical', keywords)
            self.assertGreater(len(keywords['critical']), 0)

    def test_extract_skills_marketing(self):
        """Test skill extraction for the marketing domain."""
        analysis = extract_skills(self.marketing_resume, domain='Marketing')
        # 'SEO', 'SEM', 'Google Analytics' are in marketing_keywords.json
        self.assertIn('SEO', analysis['skills'])
        self.assertIn('SEM', analysis['skills'])
        self.assertIn('Google Analytics', analysis['skills'])

if __name__ == '__main__':
    unittest.main()
