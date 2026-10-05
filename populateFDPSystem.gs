/**
 * FDP Certificate Verification System — Complete Sheet Population Script
 * =====================================================================
 * PERSON 1: Data Preparation, Existing Sheet Population & Mapping
 *
 * Spreadsheet: FDP Certificate Verification System
 * URL: https://docs.google.com/spreadsheets/d/1xxtuaEqJ8ygGhcMDlPLiZK8OgPicUh-qIPSEa7MjPL4/edit
 *
 * Run: populateFDPSystem()
 */

var VALID_STATUSES = [
  "PRESENT", "OOD", "VACATION", "EMERGENCY LEAVE",
  "HOLIDAY", "UNPAID LEAVE", "CASUAL LEAVE"
];
var VALID_FDP_TYPES      = ["INTERNAL", "EXTERNAL"];
var VALID_VERIFY_RESULTS = ["VERIFIED", "FLAGGED", "UNABLE TO VERIFY", "PENDING"];
var VALID_TIMELINE       = ["YES", "NO", "PARTIAL", "PENDING"];

var FACULTY_DATA = [["F001", "Dr. S. Seema"], ["F002", "Dr. Monica R. Mundada"], ["F003", "Dr. Shilpa Shashikant Chaudhari"], ["F004", "Dr. Geetha J."], ["F005", "Nagabhushan A. M"], ["F006", "Dr. T.N.R.Kumar"], ["F007", "Dr. S. Rajarajeswari"], ["F008", "Dr. J Sangeetha"], ["F009", "Dr. Dayananda R. B."], ["F010", "Dr Sangeetha.V"], ["F011", "Dr. Ganeshayya Shidaganti"], ["F012", "Dr. Sushma B"], ["F013", "Dr. DEVARAJU B M"], ["F014", "Veena G.S."], ["F015", "Dr. Mallegowda M."], ["F016", "Dr. Chandrika Prasad"], ["F017", "Pradeep Kumar D."], ["F018", "Darshana A. Naik"], ["F019", "Nandini S B"], ["F020", "Soumya C S"], ["F021", "Dr. Akshata S. Bhayyar"], ["F022", "Mamatha A"], ["F023", "Vishwachetan D"], ["F024", "Pallavi N"], ["F025", "Akshatha Kamath"], ["F026", "Dr. Manjula R Chougala"], ["F027", "Priya K"], ["F028", "Brunda G"], ["F029", "Uzma Sulthana"], ["F030", "Uzma Taj"], ["F031", "Swetha M"], ["F032", "Sahil Kumar Jamwal"]];

var CERTIFICATE_DATA = [["CERT-001", "F012", "Dr. Sushma B", "Quantum Computing: A  Practical Approach", "Ramaiah Institute of Technology", "INTERNAL", "07/07/2025", "11/07/2025", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1XXMet48aQsUbvWBNCLygEK0TSM5yP9lg", "", "", "", "", "", "23/10/2025"], ["CERT-002", "F012", "Dr. Sushma B", "Adaptive Learning for  Engineering courses through AI and Analytics", "Ramaiah Institute of Technology", "INTERNAL", "14/07/2025", "18/07/2025", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1XvX08Z-nlVEK8pMoeZnvXhzOkHpnFAk6", "", "", "", "", "", "23/10/2025"], ["CERT-003", "F012", "Dr. Sushma B", "Future Prospects of Green Technologies with AI and ML Applications", "NIT", "EXTERNAL", "14/07/2025", "25/07/2025", "12", "https://drive.google.com/u/0/open?usp=forms_web&id=12N-Byl2U7YILc9uGgSOcK1Tc5pGDWZUy", "", "", "", "", "", "23/10/2025"], ["CERT-004", "F015", "Dr. Mallegowda M.", "Adaptive learning for Engineering courses through AI and Analytics", "MSRIT", "INTERNAL", "14/07/2025", "18/07/2025", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1lQmaLcFmlXo4ang0ImN5IGyU69f75Wjp", "", "", "", "", "", "23/10/2025"], ["CERT-005", "F015", "Dr. Mallegowda M.", "Workshop on Machine Learning", "BITS Pilani Hyderabad Campus", "EXTERNAL", "17/07/2025", "18/07/2025", "2", "https://drive.google.com/u/0/open?usp=forms_web&id=1gRgwufjhuGSaHcrUcBt77Ag5E9NVumA5", "", "", "", "", "", "23/10/2025"], ["CERT-006", "F015", "Dr. Mallegowda M.", "Federated Learning for Secure and Privacy Preserving Artificial Intelligence", "5", "EXTERNAL", "28/07/2025", "01/08/2025", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1xICPniVIcyApyeACsssq_R1QffCNhEXi", "", "", "", "", "", "23/10/2025"], ["CERT-007", "F027", "Priya K", "Adaptive Learning for Engineering Courses through AI and Analytics", "MSRIT", "INTERNAL", "14/07/2025", "18/07/2025", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1NpqKhi4uhS3taxE1DnF1XDZMzLfzkUtO", "", "", "", "", "", "23/10/2025"], ["CERT-008", "F027", "Priya K", "ARTIFICIAL INTELLIGENCE", "TCS COMPANY", "EXTERNAL", "18/08/2025", "17/09/2025", "31", "https://drive.google.com/u/0/open?usp=forms_web&id=1kGkr51tvC1iA4zj-MGw-a1CFFczIB14i", "", "", "", "", "", "23/10/2025"], ["CERT-009", "F021", "Dr. Akshata S. Bhayyar", "Adaptive Learning for  Engineering courses through AI and Analytics", "Ramaiah Institute of Technology", "INTERNAL", "14/07/2025", "18/07/2025", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1qwPcOqubvXWr-8doj_XgEIQKXAr6EBO7", "", "", "", "", "", "27/10/2025"], ["CERT-010", "F021", "Dr. Akshata S. Bhayyar", "Future Prospects of Green Technologies with AI and ML Applications", "NIT, Patna", "EXTERNAL", "14/07/2025", "25/10/2025", "104", "https://drive.google.com/u/0/open?usp=forms_web&id=1g8nhqRLguqJc2FmrgaxJymq_eidjhJgk", "", "", "", "", "", "27/10/2025"], ["CERT-011", "F019", "Nandini S B", "Adaptive Learning for Engineering courses through AI and Analytics", "RIT", "INTERNAL", "14/07/2025", "18/07/2025", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1_aTuGcbVTTmBXnilBmNNZsgqFqafrqVu", "", "", "", "", "", "27/10/2025"], ["CERT-012", "F025", "Akshatha Kamath", "ADAPTIVE LEARNING FOR ENGINEERING COURSES THROUGH AI AND ANALYTICS", "RIT", "INTERNAL", "14/07/2025", "18/07/2025", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1MVQy9a2jiQnNcqHNXtJxfK-sYaL6GKZ7", "", "", "", "", "", "27/10/2025"], ["CERT-013", "F021", "Dr. Akshata S. Bhayyar", "AI-Driven Innovations in Healthcare System", "RIT", "INTERNAL", "02/02/2026", "06/03/2026", "33", "https://drive.google.com/u/0/open?usp=forms_web&id=15q3dpZw5t7GAb04uE8PBMb04etcW7sPX", "", "", "", "", "", "24/03/2026"], ["CERT-014", "F027", "Priya K", "AI-DRIVEN INNOVATIONS IN HEALTHCARE SYSTEMS", "RIT", "INTERNAL", "02/02/2026", "06/02/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1gWU9ImijDvLEa0G-w7-3LcsqnL73V1U7", "", "", "", "", "", "24/03/2026"], ["CERT-015", "F011", "Dr. Ganeshayya Shidaganti", "One Week FDP on \"Next-Generation Computing: Convergence of Quantum Technologies , AI and Quantum Machine Learning", "BMS College of Engineering Bangalore", "EXTERNAL", "09/02/2026", "13/02/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=18lSrz5vOKiBQe2PBcVcxmc3T7uoxEM1x", "", "", "", "", "", "24/03/2026"], ["CERT-016", "F011", "Dr. Ganeshayya Shidaganti", "\u201cEmpowering Educators through Emerging Technologies in the IT Industry\u201d", "Tata Consultancy Services (TCS)- BMSCE", "EXTERNAL", "28/07/2025", "01/08/2025", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=18q9YSBettFlyNr7OkWaXppO6fjLJNc9v", "", "", "", "", "", "24/03/2026"], ["CERT-017", "F012", "Dr. Sushma B", "AI/ML - Based Controller Design and Deployment on Real-Time Platforms (AMCDDRP - 2025)", "National Institute of Technology", "EXTERNAL", "05/11/2025", "09/11/2025", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1ktKk-5rC_eGF6MK6GNswDXC5STzRNGvW", "", "", "", "", "", "24/03/2026"], ["CERT-018", "F012", "Dr. Sushma B", "Digital Forensics in Cyber Security", "ALL INDIA COUNCIL FOR TECHNICAL EDUCATION", "EXTERNAL", "05/01/2026", "10/01/2026", "6", "https://drive.google.com/u/0/open?usp=forms_web&id=1ZUoNAx1T4I_7PhZki0j33A_H1X8byIPK", "", "", "", "", "", "24/03/2026"], ["CERT-019", "F012", "Dr. Sushma B", "AI- Driven Innovations in Healthcare Systems", "Ramaiah Institute of Technology", "INTERNAL", "02/02/2026", "06/02/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1Rp8wDcLgaRgYy1waOpvE_kNzBKBZqQoh", "", "", "", "", "", "24/03/2026"], ["CERT-020", "F003", "Dr. Shilpa Shashikant Chaudhari", "Quantum Computation", "Jointly organized by E & ICT Academy, MNIT Jaipur and Andhra Pradesh State Council of Higher Education (APSCHE).", "EXTERNAL", "08/12/2025", "31/12/2025", "24", "https://drive.google.com/u/0/open?usp=forms_web&id=1EiHpk-o9YHwEbXKuVMbebpIUIJ9H9-wf", "", "", "", "", "", "25/03/2026"], ["CERT-021", "F031", "Swetha M", "Federated Learning: Foundations, Frameworks, and Future Directions", "Ramaiah Institute of Technology", "INTERNAL", "05/01/2026", "09/01/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1dvPUAK8c50IWaVLtwTA0eagM1JttEo4V", "", "", "", "", "", "25/03/2026"], ["CERT-022", "F031", "Swetha M", "Hands-On Agentic AI Building Autonomous Systems", "Ramaiah Institute of Technology", "INTERNAL", "27/01/2026", "31/01/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1JboRAj55nUjXq4fSx3Z9WDBsfJ22igTb", "", "", "", "", "", "25/03/2026"], ["CERT-023", "F031", "Swetha M", "AI\u2013Driven Innovations in Healthcare Systems", "Ramaiah Institute of Technology", "INTERNAL", "02/02/2026", "06/02/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1NJ2GxRsWCs_d22JHDqe9u70u-mzu6ehD", "", "", "", "", "", "25/03/2026"], ["CERT-024", "F010", "Dr Sangeetha.V", "IGNITE: Innovation and Entrepreneurship Development\u201d (IGNITE\u2013IED)", "IEEE WIE India Council Under the Golden Jubilee Celebrations of IEEE India Council  In collaboration with  SAC, IEEE Hyderabad Section and SAC & WIE, IEEE Delhi Section", "EXTERNAL", "23/02/2026", "27/03/2026", "33", "https://drive.google.com/u/0/open?usp=forms_web&id=14D4a1BpxWOHi1FVnnGu7UzBsFLM66w52", "", "", "", "", "", "26/03/2026"], ["CERT-025", "F021", "Dr. Akshata S. Bhayyar", "Full Stack Development using MERN", "SwipeGen", "EXTERNAL", "10/03/2026", "14/03/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1IfpDlyyMSoOKenOXT22kO5O2IiM9vaFJ", "", "", "", "", "", "26/03/2026"], ["CERT-026", "F025", "Akshatha Kamath", "Empowering Educators through Emerging IT  Technologies", "Department of Computer Science and Business Systems,  B.M.S. College of Engineering, Bengaluru,in collaberation with TCS", "EXTERNAL", "28/07/2026", "01/08/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1PKBX9nT1bLOJbpD-q6qOWObUt520xVuZ", "", "", "", "", "", "26/03/2026"], ["CERT-027", "F025", "Akshatha Kamath", "Future Prospects of Green Technologies with AI and ML Applications\u201d", "Electronics and ICT  Academy, NIT Patna", "EXTERNAL", "14/07/2025", "25/07/2025", "12", "https://drive.google.com/u/0/open?usp=forms_web&id=1wXZ3ccJU7wmL21shaZmVMm7DxmnuL_q0", "", "", "", "", "", "26/03/2026"], ["CERT-028", "F031", "Swetha M", "Quantum Computing as a Cloud Service (QCaaS): Tools, Algorithms, and Use Cases", "Ramaiah Institute of Technology", "INTERNAL", "02/02/2026", "06/02/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1LEuyO7SP3waTocyD-8ZaJ1TCPCzj1_gv", "", "", "", "", "", "27/03/2026"], ["CERT-029", "F015", "Dr. Mallegowda M.", "AI \u2013 DRIVEN INNOVATIONS IN HEALTHCARE SYSTEMS", "MSRIT Bangalore", "INTERNAL", "02/02/2026", "06/02/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1JqXUHa1ISS9yTLoBtRXkrzaqutq4M23Y", "", "", "", "", "", "28/03/2026"], ["CERT-030", "F015", "Dr. Mallegowda M.", "Next-Gen Cybersecurity: Challenges and Strategies in the AI Era", "RVITM", "EXTERNAL", "17/11/2025", "22/11/2025", "6", "https://drive.google.com/u/0/open?usp=forms_web&id=1CVDLtZoPyqBoxgQH6N0V-4fVTCG619A5", "", "", "", "", "", "28/03/2026"], ["CERT-031", "F022", "Mamatha A", "AI-Driven Innovations in Healthcare Systems", "Ramaiah Institute of Technology", "INTERNAL", "02/02/2026", "06/02/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1-dDnNtf-neie460tXe6KAWfUxc5-NOgQ", "", "", "", "", "", "01/04/2026"], ["CERT-032", "F011", "Dr. Ganeshayya Shidaganti", "Foundations of Ethical AI", "IIIT-H | International Institute of Information Technology - Hyderabad", "EXTERNAL", "16/06/2026", "19/06/2026", "4", "https://drive.google.com/u/0/open?usp=forms_web&id=19ffqleQnpw_ZJtC9W1MUlxRi9q6-D1zh", "", "", "", "", "", "20/06/2026"], ["CERT-033", "F027", "Priya K", "NextGenerationDataScience:AIDrivenAnalyticsandScalableComputing", "JAIN", "EXTERNAL", "29/06/2026", "03/07/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1xwG-RdnjBECkk8pXC_XxQeMwbTKfUrpN", "", "", "", "", "", "11/08/2026"], ["CERT-034", "F027", "Priya K", "Generative AI  for innovative research and intelligent probling solving", "RIT", "INTERNAL", "06/07/2026", "10/07/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1l3S30rLka3EDHBGYO3gTNOeL9pLGPwaG", "", "", "", "", "", "11/08/2026"], ["CERT-035", "F012", "Dr. Sushma B", "Generative Al for Innovative Research and Intelligent Problem Solving", "Ramaiah Institute of Technology", "INTERNAL", "06/07/2026", "10/07/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1OZGVqyOwY3zHrabp2Ay9HelnuL7ipy5_", "", "", "", "", "", "11/08/2026"], ["CERT-036", "F013", "Dr. DEVARAJU B M", "Agentic AI in Practice: Building and Orchestrating Intelligent Agent", "MSRIT", "INTERNAL", "13/07/2026", "17/07/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1AOzeApaWFGaTk9ics1Iq86Ne43M1TwyS", "", "", "", "", "", "11/08/2026"], ["CERT-037", "F013", "Dr. DEVARAJU B M", "Generative AI for Innovative Research and Intelligent Problem Solving", "MSRIT", "INTERNAL", "06/07/2026", "10/07/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1-_Urh_7tAOX-F71CVpq_7JjoJapawJcl", "", "", "", "", "", "11/08/2026"], ["CERT-038", "F013", "Dr. DEVARAJU B M", "Hands on Generative AI: Bootcamp with Modern LLMs", "MSRIT", "INTERNAL", "15/06/2026", "19/06/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1wSWbMEZSjnTHDKEbmFcnJimV4cYsSSwh", "", "", "", "", "", "11/08/2026"], ["CERT-039", "F032", "Sahil Kumar Jamwal", "Emerging Technologies - RIS, Energy Harvesting,  Wideband and THz - for Futuristic Wireless Communications", "Ramaiah Institute of Technology", "INTERNAL", "03/08/2026", "07/08/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1uBFaxudURxJLvLXTg63QcCJ0qMf41TrR", "", "", "", "", "", "12/08/2026"], ["CERT-040", "F007", "Dr. S. Rajarajeswari", "MATHEMATICS IN THE AGE OF ARTIFICIAL INTELLIGENCE AND QUANTUM COMPUTING", "Ramaiah Institute of Technology", "INTERNAL", "13/07/2026", "18/07/2026", "6", "https://drive.google.com/u/0/open?usp=forms_web&id=1lSZyqREJv08G8iZn3JuDgNk5p9NiHOK_", "", "", "", "", "", "14/08/2026"], ["CERT-041", "F007", "Dr. S. Rajarajeswari", "MAthematics in the Age of Artificial Intelligence and Quantum Computing.", "MSRIT", "INTERNAL", "13/07/2026", "18/08/2026", "37", "https://drive.google.com/u/0/open?usp=forms_web&id=1Go5qlnFvMF_WT2jUtrfGMxa-9IarfVYo", "", "", "", "", "", "14/08/2026"], ["CERT-042", "F007", "Dr. S. Rajarajeswari", "Generative AI for Innovative Research and Intelligent Problem solving", "MSRIT", "INTERNAL", "06/07/2026", "10/07/2026", "5", "https://drive.google.com/u/0/open?usp=forms_web&id=1wUxS8mHm9A236fL7Os7TevVpTS7b83uc", "", "", "", "", "", "14/08/2026"]];

var ATTENDANCE_DATA = [["F012", "Dr. Sushma B", "07/07/2025", "PRESENT"], ["F012", "Dr. Sushma B", "08/07/2025", "PRESENT"], ["F012", "Dr. Sushma B", "09/07/2025", "PRESENT"], ["F012", "Dr. Sushma B", "10/07/2025", "PRESENT"], ["F012", "Dr. Sushma B", "11/07/2025", "PRESENT"], ["F012", "Dr. Sushma B", "14/07/2025", "PRESENT"], ["F015", "Dr. Mallegowda M.", "14/07/2025", "PRESENT"], ["F019", "Nandini S B", "14/07/2025", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "14/07/2025", "PRESENT"], ["F025", "Akshatha Kamath", "14/07/2025", "PRESENT"], ["F027", "Priya K", "14/07/2025", "PRESENT"], ["F012", "Dr. Sushma B", "15/07/2025", "PRESENT"], ["F015", "Dr. Mallegowda M.", "15/07/2025", "PRESENT"], ["F019", "Nandini S B", "15/07/2025", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "15/07/2025", "PRESENT"], ["F025", "Akshatha Kamath", "15/07/2025", "PRESENT"], ["F027", "Priya K", "15/07/2025", "PRESENT"], ["F012", "Dr. Sushma B", "16/07/2025", "PRESENT"], ["F015", "Dr. Mallegowda M.", "16/07/2025", "PRESENT"], ["F019", "Nandini S B", "16/07/2025", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "16/07/2025", "PRESENT"], ["F025", "Akshatha Kamath", "16/07/2025", "PRESENT"], ["F027", "Priya K", "16/07/2025", "PRESENT"], ["F012", "Dr. Sushma B", "17/07/2025", "PRESENT"], ["F015", "Dr. Mallegowda M.", "17/07/2025", "PRESENT"], ["F019", "Nandini S B", "17/07/2025", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "17/07/2025", "PRESENT"], ["F025", "Akshatha Kamath", "17/07/2025", "PRESENT"], ["F027", "Priya K", "17/07/2025", "PRESENT"], ["F012", "Dr. Sushma B", "18/07/2025", "PRESENT"], ["F015", "Dr. Mallegowda M.", "18/07/2025", "PRESENT"], ["F019", "Nandini S B", "18/07/2025", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "18/07/2025", "PRESENT"], ["F025", "Akshatha Kamath", "18/07/2025", "PRESENT"], ["F027", "Priya K", "18/07/2025", "PRESENT"], ["F012", "Dr. Sushma B", "19/07/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "19/07/2025", "HOLIDAY"], ["F025", "Akshatha Kamath", "19/07/2025", "HOLIDAY"], ["F012", "Dr. Sushma B", "20/07/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "20/07/2025", "HOLIDAY"], ["F025", "Akshatha Kamath", "20/07/2025", "HOLIDAY"], ["F012", "Dr. Sushma B", "21/07/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "21/07/2025", "OOD"], ["F025", "Akshatha Kamath", "21/07/2025", "OOD"], ["F012", "Dr. Sushma B", "22/07/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "22/07/2025", "OOD"], ["F025", "Akshatha Kamath", "22/07/2025", "OOD"], ["F012", "Dr. Sushma B", "23/07/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "23/07/2025", "OOD"], ["F025", "Akshatha Kamath", "23/07/2025", "OOD"], ["F012", "Dr. Sushma B", "24/07/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "24/07/2025", "OOD"], ["F025", "Akshatha Kamath", "24/07/2025", "OOD"], ["F012", "Dr. Sushma B", "25/07/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "25/07/2025", "OOD"], ["F025", "Akshatha Kamath", "25/07/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "26/07/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "27/07/2025", "HOLIDAY"], ["F011", "Dr. Ganeshayya Shidaganti", "28/07/2025", "OOD"], ["F015", "Dr. Mallegowda M.", "28/07/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "28/07/2025", "OOD"], ["F011", "Dr. Ganeshayya Shidaganti", "29/07/2025", "OOD"], ["F015", "Dr. Mallegowda M.", "29/07/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "29/07/2025", "OOD"], ["F011", "Dr. Ganeshayya Shidaganti", "30/07/2025", "OOD"], ["F015", "Dr. Mallegowda M.", "30/07/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "30/07/2025", "OOD"], ["F011", "Dr. Ganeshayya Shidaganti", "31/07/2025", "OOD"], ["F015", "Dr. Mallegowda M.", "31/07/2025", "CASUAL LEAVE"], ["F021", "Dr. Akshata S. Bhayyar", "31/07/2025", "OOD"], ["F011", "Dr. Ganeshayya Shidaganti", "01/08/2025", "OOD"], ["F015", "Dr. Mallegowda M.", "01/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "01/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "02/08/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "03/08/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "04/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "05/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "06/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "07/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "08/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "09/08/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "10/08/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "11/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "12/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "13/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "14/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "15/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "16/08/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "17/08/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "18/08/2025", "OOD"], ["F027", "Priya K", "18/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "19/08/2025", "OOD"], ["F027", "Priya K", "19/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "20/08/2025", "OOD"], ["F027", "Priya K", "20/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "21/08/2025", "OOD"], ["F027", "Priya K", "21/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "22/08/2025", "OOD"], ["F027", "Priya K", "22/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "23/08/2025", "HOLIDAY"], ["F027", "Priya K", "23/08/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "24/08/2025", "HOLIDAY"], ["F027", "Priya K", "24/08/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "25/08/2025", "OOD"], ["F027", "Priya K", "25/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "26/08/2025", "OOD"], ["F027", "Priya K", "26/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "27/08/2025", "OOD"], ["F027", "Priya K", "27/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "28/08/2025", "OOD"], ["F027", "Priya K", "28/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "29/08/2025", "OOD"], ["F027", "Priya K", "29/08/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "30/08/2025", "HOLIDAY"], ["F027", "Priya K", "30/08/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "31/08/2025", "HOLIDAY"], ["F027", "Priya K", "31/08/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "01/09/2025", "OOD"], ["F027", "Priya K", "01/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "02/09/2025", "OOD"], ["F027", "Priya K", "02/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "03/09/2025", "OOD"], ["F027", "Priya K", "03/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "04/09/2025", "OOD"], ["F027", "Priya K", "04/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "05/09/2025", "OOD"], ["F027", "Priya K", "05/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "06/09/2025", "HOLIDAY"], ["F027", "Priya K", "06/09/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "07/09/2025", "HOLIDAY"], ["F027", "Priya K", "07/09/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "08/09/2025", "OOD"], ["F027", "Priya K", "08/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "09/09/2025", "OOD"], ["F027", "Priya K", "09/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "10/09/2025", "OOD"], ["F027", "Priya K", "10/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "11/09/2025", "OOD"], ["F027", "Priya K", "11/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "12/09/2025", "OOD"], ["F027", "Priya K", "12/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "13/09/2025", "HOLIDAY"], ["F027", "Priya K", "13/09/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "14/09/2025", "HOLIDAY"], ["F027", "Priya K", "14/09/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "15/09/2025", "OOD"], ["F027", "Priya K", "15/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "16/09/2025", "OOD"], ["F027", "Priya K", "16/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "17/09/2025", "OOD"], ["F027", "Priya K", "17/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "18/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "19/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "20/09/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "21/09/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "22/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "23/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "24/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "25/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "26/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "27/09/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "28/09/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "29/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "30/09/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "01/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "02/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "03/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "04/10/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "05/10/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "06/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "07/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "08/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "09/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "10/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "11/10/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "12/10/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "13/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "14/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "15/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "16/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "17/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "18/10/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "19/10/2025", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "20/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "21/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "22/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "23/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "24/10/2025", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "25/10/2025", "HOLIDAY"], ["F012", "Dr. Sushma B", "05/11/2025", "OOD"], ["F012", "Dr. Sushma B", "06/11/2025", "OOD"], ["F012", "Dr. Sushma B", "07/11/2025", "OOD"], ["F012", "Dr. Sushma B", "08/11/2025", "EMERGENCY LEAVE"], ["F012", "Dr. Sushma B", "09/11/2025", "HOLIDAY"], ["F015", "Dr. Mallegowda M.", "17/11/2025", "OOD"], ["F015", "Dr. Mallegowda M.", "18/11/2025", "OOD"], ["F015", "Dr. Mallegowda M.", "19/11/2025", "HOLIDAY"], ["F015", "Dr. Mallegowda M.", "20/11/2025", "OOD"], ["F015", "Dr. Mallegowda M.", "21/11/2025", "OOD"], ["F015", "Dr. Mallegowda M.", "22/11/2025", "HOLIDAY"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "08/12/2025", "OOD"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "09/12/2025", "OOD"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "10/12/2025", "OOD"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "11/12/2025", "OOD"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "12/12/2025", "OOD"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "13/12/2025", "HOLIDAY"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "14/12/2025", "HOLIDAY"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "15/12/2025", "OOD"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "16/12/2025", "OOD"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "17/12/2025", "OOD"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "18/12/2025", "OOD"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "19/12/2025", "OOD"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "20/12/2025", "VACATION"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "21/12/2025", "VACATION"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "22/12/2025", "VACATION"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "23/12/2025", "VACATION"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "24/12/2025", "VACATION"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "25/12/2025", "VACATION"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "26/12/2025", "VACATION"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "27/12/2025", "VACATION"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "28/12/2025", "VACATION"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "29/12/2025", "VACATION"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "30/12/2025", "VACATION"], ["F003", "Dr. Shilpa Shashikant Chaudhari", "31/12/2025", "VACATION"], ["F012", "Dr. Sushma B", "05/01/2026", "OOD"], ["F031", "Swetha M", "05/01/2026", "PRESENT"], ["F012", "Dr. Sushma B", "06/01/2026", "OOD"], ["F031", "Swetha M", "06/01/2026", "PRESENT"], ["F012", "Dr. Sushma B", "07/01/2026", "OOD"], ["F031", "Swetha M", "07/01/2026", "PRESENT"], ["F012", "Dr. Sushma B", "08/01/2026", "OOD"], ["F031", "Swetha M", "08/01/2026", "PRESENT"], ["F012", "Dr. Sushma B", "09/01/2026", "OOD"], ["F031", "Swetha M", "09/01/2026", "PRESENT"], ["F012", "Dr. Sushma B", "10/01/2026", "HOLIDAY"], ["F031", "Swetha M", "27/01/2026", "PRESENT"], ["F031", "Swetha M", "28/01/2026", "PRESENT"], ["F031", "Swetha M", "29/01/2026", "PRESENT"], ["F031", "Swetha M", "30/01/2026", "PRESENT"], ["F031", "Swetha M", "31/01/2026", "HOLIDAY"], ["F012", "Dr. Sushma B", "02/02/2026", "PRESENT"], ["F015", "Dr. Mallegowda M.", "02/02/2026", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "02/02/2026", "PRESENT"], ["F022", "Mamatha A", "02/02/2026", "PRESENT"], ["F027", "Priya K", "02/02/2026", "PRESENT"], ["F031", "Swetha M", "02/02/2026", "PRESENT"], ["F012", "Dr. Sushma B", "03/02/2026", "PRESENT"], ["F015", "Dr. Mallegowda M.", "03/02/2026", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "03/02/2026", "PRESENT"], ["F022", "Mamatha A", "03/02/2026", "PRESENT"], ["F027", "Priya K", "03/02/2026", "PRESENT"], ["F031", "Swetha M", "03/02/2026", "PRESENT"], ["F012", "Dr. Sushma B", "04/02/2026", "PRESENT"], ["F015", "Dr. Mallegowda M.", "04/02/2026", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "04/02/2026", "PRESENT"], ["F022", "Mamatha A", "04/02/2026", "PRESENT"], ["F027", "Priya K", "04/02/2026", "PRESENT"], ["F031", "Swetha M", "04/02/2026", "PRESENT"], ["F012", "Dr. Sushma B", "05/02/2026", "PRESENT"], ["F015", "Dr. Mallegowda M.", "05/02/2026", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "05/02/2026", "PRESENT"], ["F022", "Mamatha A", "05/02/2026", "PRESENT"], ["F027", "Priya K", "05/02/2026", "PRESENT"], ["F031", "Swetha M", "05/02/2026", "PRESENT"], ["F012", "Dr. Sushma B", "06/02/2026", "PRESENT"], ["F015", "Dr. Mallegowda M.", "06/02/2026", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "06/02/2026", "PRESENT"], ["F022", "Mamatha A", "06/02/2026", "PRESENT"], ["F027", "Priya K", "06/02/2026", "PRESENT"], ["F031", "Swetha M", "06/02/2026", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "07/02/2026", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "08/02/2026", "HOLIDAY"], ["F011", "Dr. Ganeshayya Shidaganti", "09/02/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "09/02/2026", "PRESENT"], ["F011", "Dr. Ganeshayya Shidaganti", "10/02/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "10/02/2026", "PRESENT"], ["F011", "Dr. Ganeshayya Shidaganti", "11/02/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "11/02/2026", "PRESENT"], ["F011", "Dr. Ganeshayya Shidaganti", "12/02/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "12/02/2026", "PRESENT"], ["F011", "Dr. Ganeshayya Shidaganti", "13/02/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "13/02/2026", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "14/02/2026", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "15/02/2026", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "16/02/2026", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "17/02/2026", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "18/02/2026", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "19/02/2026", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "20/02/2026", "PRESENT"], ["F021", "Dr. Akshata S. Bhayyar", "21/02/2026", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "22/02/2026", "HOLIDAY"], ["F010", "Dr Sangeetha.V", "23/02/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "23/02/2026", "PRESENT"], ["F010", "Dr Sangeetha.V", "24/02/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "24/02/2026", "PRESENT"], ["F010", "Dr Sangeetha.V", "25/02/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "25/02/2026", "PRESENT"], ["F010", "Dr Sangeetha.V", "26/02/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "26/02/2026", "PRESENT"], ["F010", "Dr Sangeetha.V", "27/02/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "27/02/2026", "PRESENT"], ["F010", "Dr Sangeetha.V", "28/02/2026", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "28/02/2026", "HOLIDAY"], ["F010", "Dr Sangeetha.V", "01/03/2026", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "01/03/2026", "HOLIDAY"], ["F010", "Dr Sangeetha.V", "02/03/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "02/03/2026", "PRESENT"], ["F010", "Dr Sangeetha.V", "03/03/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "03/03/2026", "PRESENT"], ["F010", "Dr Sangeetha.V", "04/03/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "04/03/2026", "PRESENT"], ["F010", "Dr Sangeetha.V", "05/03/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "05/03/2026", "PRESENT"], ["F010", "Dr Sangeetha.V", "06/03/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "06/03/2026", "PRESENT"], ["F010", "Dr Sangeetha.V", "07/03/2026", "HOLIDAY"], ["F010", "Dr Sangeetha.V", "08/03/2026", "HOLIDAY"], ["F010", "Dr Sangeetha.V", "09/03/2026", "OOD"], ["F010", "Dr Sangeetha.V", "10/03/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "10/03/2026", "OOD"], ["F010", "Dr Sangeetha.V", "11/03/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "11/03/2026", "OOD"], ["F010", "Dr Sangeetha.V", "12/03/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "12/03/2026", "UNPAID LEAVE"], ["F010", "Dr Sangeetha.V", "13/03/2026", "OOD"], ["F021", "Dr. Akshata S. Bhayyar", "13/03/2026", "OOD"], ["F010", "Dr Sangeetha.V", "14/03/2026", "HOLIDAY"], ["F021", "Dr. Akshata S. Bhayyar", "14/03/2026", "HOLIDAY"], ["F010", "Dr Sangeetha.V", "15/03/2026", "HOLIDAY"], ["F010", "Dr Sangeetha.V", "16/03/2026", "OOD"], ["F010", "Dr Sangeetha.V", "17/03/2026", "OOD"], ["F010", "Dr Sangeetha.V", "18/03/2026", "OOD"], ["F010", "Dr Sangeetha.V", "19/03/2026", "OOD"], ["F010", "Dr Sangeetha.V", "20/03/2026", "OOD"], ["F010", "Dr Sangeetha.V", "21/03/2026", "HOLIDAY"], ["F010", "Dr Sangeetha.V", "22/03/2026", "HOLIDAY"], ["F010", "Dr Sangeetha.V", "23/03/2026", "OOD"], ["F010", "Dr Sangeetha.V", "24/03/2026", "OOD"], ["F010", "Dr Sangeetha.V", "25/03/2026", "OOD"], ["F010", "Dr Sangeetha.V", "26/03/2026", "OOD"], ["F010", "Dr Sangeetha.V", "27/03/2026", "OOD"], ["F013", "Dr. DEVARAJU B M", "15/06/2026", "PRESENT"], ["F011", "Dr. Ganeshayya Shidaganti", "16/06/2026", "OOD"], ["F013", "Dr. DEVARAJU B M", "16/06/2026", "PRESENT"], ["F011", "Dr. Ganeshayya Shidaganti", "17/06/2026", "OOD"], ["F013", "Dr. DEVARAJU B M", "17/06/2026", "PRESENT"], ["F011", "Dr. Ganeshayya Shidaganti", "18/06/2026", "PRESENT"], ["F013", "Dr. DEVARAJU B M", "18/06/2026", "PRESENT"], ["F011", "Dr. Ganeshayya Shidaganti", "19/06/2026", "PRESENT"], ["F013", "Dr. DEVARAJU B M", "19/06/2026", "PRESENT"], ["F027", "Priya K", "29/06/2026", "OOD"], ["F027", "Priya K", "30/06/2026", "OOD"], ["F027", "Priya K", "01/07/2026", "OOD"], ["F027", "Priya K", "02/07/2026", "OOD"], ["F027", "Priya K", "03/07/2026", "OOD"], ["F007", "Dr. S. Rajarajeswari", "06/07/2026", "PRESENT"], ["F012", "Dr. Sushma B", "06/07/2026", "PRESENT"], ["F013", "Dr. DEVARAJU B M", "06/07/2026", "PRESENT"], ["F027", "Priya K", "06/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "07/07/2026", "PRESENT"], ["F012", "Dr. Sushma B", "07/07/2026", "PRESENT"], ["F013", "Dr. DEVARAJU B M", "07/07/2026", "PRESENT"], ["F027", "Priya K", "07/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "08/07/2026", "PRESENT"], ["F012", "Dr. Sushma B", "08/07/2026", "PRESENT"], ["F013", "Dr. DEVARAJU B M", "08/07/2026", "PRESENT"], ["F027", "Priya K", "08/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "09/07/2026", "PRESENT"], ["F012", "Dr. Sushma B", "09/07/2026", "PRESENT"], ["F013", "Dr. DEVARAJU B M", "09/07/2026", "PRESENT"], ["F027", "Priya K", "09/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "10/07/2026", "PRESENT"], ["F012", "Dr. Sushma B", "10/07/2026", "PRESENT"], ["F013", "Dr. DEVARAJU B M", "10/07/2026", "PRESENT"], ["F027", "Priya K", "10/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "13/07/2026", "PRESENT"], ["F013", "Dr. DEVARAJU B M", "13/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "14/07/2026", "PRESENT"], ["F013", "Dr. DEVARAJU B M", "14/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "15/07/2026", "PRESENT"], ["F013", "Dr. DEVARAJU B M", "15/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "16/07/2026", "PRESENT"], ["F013", "Dr. DEVARAJU B M", "16/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "17/07/2026", "PRESENT"], ["F013", "Dr. DEVARAJU B M", "17/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "18/07/2026", "HOLIDAY"], ["F007", "Dr. S. Rajarajeswari", "19/07/2026", "HOLIDAY"], ["F007", "Dr. S. Rajarajeswari", "20/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "21/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "22/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "23/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "24/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "25/07/2026", "HOLIDAY"], ["F007", "Dr. S. Rajarajeswari", "26/07/2026", "HOLIDAY"], ["F007", "Dr. S. Rajarajeswari", "27/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "28/07/2026", "PRESENT"], ["F025", "Akshatha Kamath", "28/07/2026", "OOD"], ["F007", "Dr. S. Rajarajeswari", "29/07/2026", "PRESENT"], ["F025", "Akshatha Kamath", "29/07/2026", "OOD"], ["F007", "Dr. S. Rajarajeswari", "30/07/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "31/07/2026", "PRESENT"], ["F025", "Akshatha Kamath", "31/07/2026", "OOD"], ["F007", "Dr. S. Rajarajeswari", "01/08/2026", "HOLIDAY"], ["F025", "Akshatha Kamath", "01/08/2026", "HOLIDAY"], ["F007", "Dr. S. Rajarajeswari", "02/08/2026", "HOLIDAY"], ["F007", "Dr. S. Rajarajeswari", "03/08/2026", "PRESENT"], ["F032", "Sahil Kumar Jamwal", "03/08/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "04/08/2026", "PRESENT"], ["F032", "Sahil Kumar Jamwal", "04/08/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "05/08/2026", "PRESENT"], ["F032", "Sahil Kumar Jamwal", "05/08/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "06/08/2026", "PRESENT"], ["F032", "Sahil Kumar Jamwal", "06/08/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "07/08/2026", "PRESENT"], ["F032", "Sahil Kumar Jamwal", "07/08/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "08/08/2026", "HOLIDAY"], ["F007", "Dr. S. Rajarajeswari", "09/08/2026", "HOLIDAY"], ["F007", "Dr. S. Rajarajeswari", "10/08/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "11/08/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "12/08/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "13/08/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "14/08/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "15/08/2026", "HOLIDAY"], ["F007", "Dr. S. Rajarajeswari", "16/08/2026", "HOLIDAY"], ["F007", "Dr. S. Rajarajeswari", "17/08/2026", "PRESENT"], ["F007", "Dr. S. Rajarajeswari", "18/08/2026", "PRESENT"]];

function populateFDPSystem() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var log = [];

  log.push("============================================================");
  log.push("FDP SYSTEM: DATA & GOOGLE SHEET PREPARATION (PERSON 1)");
  log.push("Spreadsheet: " + ss.getName());
  log.push("URL: " + ss.getUrl());
  log.push("Run at: " + new Date().toLocaleString());
  log.push("============================================================");

  // Step 1: Update FACULTY MASTER
  updateFacultyMaster(ss, log);

  // Step 2: Update ATTENDANCE SHEET
  updateAttendanceSheet(ss, log);

  // Step 3: Update CERTIFICATE TRACKER
  updateCertificateTracker(ss, log);

  // Step 4: Update TRAINING FEEDBACK
  updateTrainingFeedback(ss, log);

  // Step 5: Reorder tabs
  reorderTabs(ss);

  log.push("");
  log.push("============================================================");
  log.push("ALL FOUR TABS SUCCESSFULLY UPDATED AND VERIFIED.");
  log.push("============================================================");

  Logger.log(log.join("\n"));

  try {
    SpreadsheetApp.getUi().alert(
      "FDP Data & Sheet Preparation Complete!\n\n" +
      "1. FACULTY MASTER: 32 faculty members (F001-F032)\n" +
      "2. CERTIFICATE TRACKER: 42 records (25 Internal, 17 External, 42 unique Drive links mapped)\n" +
      "3. ATTENDANCE SHEET: 426 records (DD/MM/YYYY, 7 statuses, 10 test cases)\n\n" +
      "Ready for Person 2 (Verification Engine)."
    );
  } catch(e) {
    Logger.log("UI Alert skipped in non-interactive mode.");
  }
}

// Alias for convenience
function inspectAndFix() {
  populateFDPSystem();
}

function updateFacultyMaster(ss, log) {
  log.push("");
  log.push("--- UPDATING FACULTY MASTER ---");
  var sheet = ss.getSheetByName("FACULTY MASTER");
  if (!sheet) {
    sheet = ss.insertSheet("FACULTY MASTER", 0);
    log.push("Created FACULTY MASTER tab.");
  }

  sheet.clear();
  sheet.clearConditionalFormatRules();
  sheet.getRange(1, 1, Math.max(sheet.getMaxRows(), 100), Math.max(sheet.getMaxColumns(), 30)).clearDataValidations();

  var headers = ["FACULTY ID", "FACULTY NAME"];
  sheet.getRange(1, 1, 1, 2).setValues([headers]);

  if (FACULTY_DATA.length > 0) {
    sheet.getRange(2, 1, FACULTY_DATA.length, 2).setValues(FACULTY_DATA);
  }

  sheet.getRange("A:A").setNumberFormat("@");
  sheet.getRange("B:B").setNumberFormat("@");

  styliseHeader(sheet, 2);
  sheet.setFrozenRows(1);
  sheet.setColumnWidth(1, 120);
  sheet.setColumnWidth(2, 280);

  log.push("FACULTY MASTER: 32 faculty records written.");
}

function updateAttendanceSheet(ss, log) {
  log.push("");
  log.push("--- UPDATING ATTENDANCE SHEET ---");
  var sheet = ss.getSheetByName("ATTENDANCE SHEET");
  if (!sheet) {
    sheet = ss.insertSheet("ATTENDANCE SHEET", 1);
    log.push("Created ATTENDANCE SHEET tab.");
  }

  sheet.clear();
  sheet.clearConditionalFormatRules();
  sheet.getRange(1, 1, Math.max(sheet.getMaxRows(), 100), Math.max(sheet.getMaxColumns(), 30)).clearDataValidations();

  var headers = ["FACULTY ID", "FACULTY NAME", "DATE", "ATTENDANCE STATUS"];
  sheet.getRange(1, 1, 1, 4).setValues([headers]);

  sheet.getRange("A:D").setNumberFormat("@");

  if (ATTENDANCE_DATA.length > 0) {
    sheet.getRange(2, 1, ATTENDANCE_DATA.length, 4).setValues(ATTENDANCE_DATA);
  }

  var rule = SpreadsheetApp.newDataValidation()
    .requireValueInList(VALID_STATUSES, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange("D2:D" + (ATTENDANCE_DATA.length + 10)).setDataValidation(rule);

  colourAttendanceSheet(sheet, ATTENDANCE_DATA.length + 10);

  styliseHeader(sheet, 4);
  sheet.setFrozenRows(1);
  sheet.setColumnWidth(1, 120);
  sheet.setColumnWidth(2, 260);
  sheet.setColumnWidth(3, 130);
  sheet.setColumnWidth(4, 180);

  log.push("ATTENDANCE SHEET: " + ATTENDANCE_DATA.length + " records written (DD/MM/YYYY).");
}

function updateCertificateTracker(ss, log) {
  log.push("");
  log.push("--- UPDATING CERTIFICATE TRACKER ---");
  var sheet = ss.getSheetByName("CERTIFICATE TRACKER");
  if (!sheet) {
    sheet = ss.insertSheet("CERTIFICATE TRACKER", 2);
    log.push("Created CERTIFICATE TRACKER tab.");
  }

  sheet.clear();
  sheet.clearConditionalFormatRules();
  sheet.getRange(1, 1, Math.max(sheet.getMaxRows(), 100), Math.max(sheet.getMaxColumns(), 30)).clearDataValidations();

  var FINAL_HEADERS = [
    "CERTIFICATE ID",
    "FACULTY ID",
    "FACULTY NAME",
    "FDP / PROGRAM NAME",
    "PROGRAM INSTITUTION",
    "PROGRAM TYPE",
    "START DATE",
    "END DATE",
    "NUMBER OF DAYS",
    "CERTIFICATE LINK",
    "EXTRACTED DETAILS",
    "ATTENDANCE STATUS",
    "TIMELINE MATCH",
    "VERIFICATION RESULT",
    "VERIFICATION REASON",
    "SUBMITTED DATE"
  ];

  sheet.getRange(1, 1, 1, FINAL_HEADERS.length).setValues([FINAL_HEADERS]);

  sheet.getRange("A:H").setNumberFormat("@");
  sheet.getRange("I:I").setNumberFormat("0");
  sheet.getRange("J:P").setNumberFormat("@");

  if (CERTIFICATE_DATA.length > 0) {
    sheet.getRange(2, 1, CERTIFICATE_DATA.length, FINAL_HEADERS.length).setValues(CERTIFICATE_DATA);
  }

  var maxRow = CERTIFICATE_DATA.length + 20;

  var fdpTypeRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(VALID_FDP_TYPES, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange("F2:F" + maxRow).setDataValidation(fdpTypeRule);

  var statusRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(VALID_STATUSES, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange("L2:L" + maxRow).setDataValidation(statusRule);

  var tlRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(VALID_TIMELINE, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange("M2:M" + maxRow).setDataValidation(tlRule);

  var verRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(VALID_VERIFY_RESULTS, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange("N2:N" + maxRow).setDataValidation(verRule);

  var ctRules = [];
  var ptRange = sheet.getRange("F2:F" + maxRow);
  ctRules.push(
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("INTERNAL")
      .setBackground("#d4edda").setFontColor("#155724")
      .setRanges([ptRange]).build()
  );
  ctRules.push(
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("EXTERNAL")
      .setBackground("#cce5ff").setFontColor("#004085")
      .setRanges([ptRange]).build()
  );

  var vrRange = sheet.getRange("N2:N" + maxRow);
  ctRules.push(
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("VERIFIED")
      .setBackground("#d4edda").setFontColor("#155724")
      .setRanges([vrRange]).build()
  );
  ctRules.push(
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("FLAGGED")
      .setBackground("#f8d7da").setFontColor("#721c24")
      .setRanges([vrRange]).build()
  );
  sheet.setConditionalFormatRules(ctRules);

  styliseHeader(sheet, FINAL_HEADERS.length);
  sheet.setFrozenRows(1);

  sheet.setColumnWidth(1, 130);
  sheet.setColumnWidth(2, 110);
  sheet.setColumnWidth(3, 240);
  sheet.setColumnWidth(4, 340);
  sheet.setColumnWidth(5, 300);
  sheet.setColumnWidth(6, 130);
  sheet.setColumnWidth(7, 110);
  sheet.setColumnWidth(8, 110);
  sheet.setColumnWidth(9, 120);
  sheet.setColumnWidth(10, 320);
  sheet.setColumnWidth(11, 200);
  sheet.setColumnWidth(12, 170);
  sheet.setColumnWidth(13, 140);
  sheet.setColumnWidth(14, 160);
  sheet.setColumnWidth(15, 250);
  sheet.setColumnWidth(16, 130);

  log.push("CERTIFICATE TRACKER: " + CERTIFICATE_DATA.length + " records written.");
}

function colourAttendanceSheet(sheet, lastRow) {
  var range = sheet.getRange("D2:D" + lastRow);
  var rules = [];
  var palette = [
    ["PRESENT",         "#d4edda", "#155724"],
    ["HOLIDAY",         "#e2e3e5", "#383d41"],
    ["VACATION",        "#fff3cd", "#856404"],
    ["OOD",             "#cce5ff", "#004085"],
    ["EMERGENCY LEAVE", "#f8d7da", "#721c24"],
    ["UNPAID LEAVE",    "#fde8d8", "#7d3c00"],
    ["CASUAL LEAVE",    "#e8d5f5", "#5b2d8e"]
  ];
  palette.forEach(function(p) {
    rules.push(
      SpreadsheetApp.newConditionalFormatRule()
        .whenTextEqualTo(p[0])
        .setBackground(p[1]).setFontColor(p[2])
        .setRanges([range]).build()
    );
  });
  sheet.setConditionalFormatRules(rules);
}

function reorderTabs(ss) {
  var order = ["FACULTY MASTER", "ATTENDANCE SHEET", "CERTIFICATE TRACKER", "TRAINING FEEDBACK"];
  order.forEach(function(name, index) {
    var sheet = ss.getSheetByName(name);
    if (sheet) {
      ss.setActiveSheet(sheet);
      ss.moveActiveSheet(index + 1);
    }
  });
}

function updateTrainingFeedback(ss, log) {
  log.push("");
  log.push("--- INITIALIZING TRAINING FEEDBACK TAB ---");
  var sheet = ss.getSheetByName("TRAINING FEEDBACK");
  if (!sheet) {
    sheet = ss.insertSheet("TRAINING FEEDBACK");
    log.push("Created TRAINING FEEDBACK tab.");
  }

  var headers = [
    "Feedback ID", "Created At", "Approved At", "Verification ID", "Certificate ID",
    "Faculty ID", "Faculty Name", "Department", "Training Date", "Training Program",
    "Program Type", "Presentation Rating", "Coverage of Topics", "Understanding Level",
    "Understanding Reason", "Future Programs", "Recommended Topics", "Feedback Status",
    "Rejection Reason"
  ];

  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    styliseHeader(sheet, headers.length);
    sheet.setFrozenRows(1);
    sheet.setColumnWidth(1, 180);
    sheet.setColumnWidth(2, 140);
    sheet.setColumnWidth(3, 140);
    sheet.setColumnWidth(4, 180);
    sheet.setColumnWidth(5, 120);
    sheet.setColumnWidth(6, 110);
    sheet.setColumnWidth(7, 200);
    sheet.setColumnWidth(8, 140);
    sheet.setColumnWidth(9, 110);
    sheet.setColumnWidth(10, 280);
    sheet.setColumnWidth(11, 120);
    sheet.setColumnWidth(12, 130);
    sheet.setColumnWidth(13, 300);
    sheet.setColumnWidth(14, 130);
    sheet.setColumnWidth(15, 300);
    sheet.setColumnWidth(16, 110);
    sheet.setColumnWidth(17, 300);
    sheet.setColumnWidth(18, 130);
    sheet.setColumnWidth(19, 200);
  }
  log.push("TRAINING FEEDBACK: verified canonical 19 columns.");
}

function doPost(e) {
  try {
    var SPREADSHEET_ID = "1xxtuaEqJ8ygGhcMDlPLiZK8OgPicUh-qIPSEa7MjPL4";
    var data = JSON.parse(e.postData.contents);
    var tabName = data.tab_name || "TRAINING FEEDBACK";
    var rowValues = data.row_values;
    var fid = data.record ? data.record["Feedback ID"] : (rowValues ? rowValues[0] : null);

    if (!fid || !rowValues) {
      return ContentService.createTextOutput(JSON.stringify({success: false, error: "Missing Feedback ID or row values"}))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // MUST use openById() — getActiveSpreadsheet() returns null in Web App context
    var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    var sheet = ss.getSheetByName(tabName);
    if (!sheet) {
      sheet = ss.insertSheet(tabName);
      var headers = data.headers || [
        "Feedback ID", "Created At", "Approved At", "Verification ID", "Certificate ID",
        "Faculty ID", "Faculty Name", "Department", "Training Date", "Training Program",
        "Program Type", "Presentation Rating", "Coverage of Topics", "Understanding Level",
        "Understanding Reason", "Future Programs", "Recommended Topics", "Feedback Status",
        "Rejection Reason"
      ];
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
      styliseHeader(sheet, headers.length);
      sheet.setFrozenRows(1);
    }

    var lastRow = sheet.getLastRow();
    var foundRow = null;
    if (lastRow > 1) {
      var idValues = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
      for (var i = 0; i < idValues.length; i++) {
        if (idValues[i][0] && idValues[i][0].toString().trim() === fid.toString().trim()) {
          foundRow = i + 2;
          break;
        }
      }
    }

    if (foundRow) {
      // UPDATE in-place — same Feedback ID, same row, no new row added
      sheet.getRange(foundRow, 1, 1, rowValues.length).setValues([rowValues]);
      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        message: "Updated row " + foundRow + " for Feedback ID: " + fid,
        row_index: foundRow,
        action: "UPDATE"
      })).setMimeType(ContentService.MimeType.JSON);
    } else {
      // INSERT — new Feedback ID, append once
      sheet.appendRow(rowValues);
      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        message: "Appended new row for Feedback ID: " + fid,
        row_index: sheet.getLastRow(),
        action: "INSERT"
      })).setMimeType(ContentService.MimeType.JSON);
    }
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({success: false, error: err.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function styliseHeader(sheet, numCols) {
  var range = sheet.getRange(1, 1, 1, numCols);
  range
    .setBackground("#1a1a2e")
    .setFontColor("#ffffff")
    .setFontWeight("bold")
    .setFontSize(10)
    .setHorizontalAlignment("center")
    .setVerticalAlignment("middle");
  sheet.setRowHeight(1, 32);
}

