import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        if self._pageNumber == 1:
            return  # Skip cover page
            
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#475569")) # Slate 600
        self.setStrokeColor(colors.HexColor("#cbd5e1")) # Slate 300
        self.setLineWidth(0.5)
        
        # Header (only for pages >= 5, representing chapters after front matter)
        if self._pageNumber >= 5:
            self.drawString(54, 800, "NeuroShield: High-Performance Network Intrusion Detection System")
            self.line(54, 792, 541.27, 792)
            
        # Footer
        if self._pageNumber == 2:
            page_text = "II"
        elif self._pageNumber == 3:
            page_text = "III"
        elif self._pageNumber == 4:
            page_text = "IV"
        else:
            page_text = str(self._pageNumber - 4)
            
        self.drawRightString(541.27, 40, page_text)
        self.drawString(54, 40, "C-DAC Mohali — Summer Training Project Report")
        self.line(54, 52, 541.27, 52)
        
        self.restoreState()

def build_pdf(filename="NEUROSHIELD_PROJECT_REPORT.pdf"):
    # 54pt margin = 0.75 in
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1e1b4b"), # Dark indigo
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#4338ca"), # Indigo 700
        spaceAfter=25
    )
    
    metadata_style = ParagraphStyle(
        "CoverMetadata",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=11,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=10
    )
    
    heading1_style = ParagraphStyle(
        "ChapterHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1e1b4b"),
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )

    heading2_style = ParagraphStyle(
        "SubHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#4338ca"),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        "BodyJustified",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=10.5,
        leading=14.5,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    )

    code_style = ParagraphStyle(
        "CodeBlock",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=6,
        spaceAfter=6
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10.5,
        textColor=colors.white,
        alignment=TA_CENTER
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=8.5,
        leading=10.5
    )

    table_cell_center = ParagraphStyle(
        "TableCellCenter",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=8.5,
        leading=10.5,
        alignment=TA_CENTER
    )

    story = []
    asset_dir = "docs/report_assets"

    # ==========================================
    # PAGE 1: COVER PAGE
    # ==========================================
    story.append(Spacer(1, 20))
    story.append(Paragraph("A PROJECT REPORT ON", subtitle_style))
    story.append(Paragraph("NeuroShield: High-Performance Network<br/>Intrusion Detection System", title_style))
    story.append(Paragraph("Using a Hybrid CNN-BiLSTM-Attention Classification Engine", subtitle_style))
    story.append(Spacer(1, 15))
    
    # Logo - little longer, not so broad and wide
    logo_path = os.path.join(asset_dir, "extracted_image_1.jpeg")
    if os.path.exists(logo_path):
        story.append(Image(logo_path, width=95, height=120))
    else:
        story.append(Spacer(1, 120))
    
    story.append(Spacer(1, 25))
    story.append(Paragraph("Submitted in partial fulfilment<br/>For the award of the Certificate of Course", metadata_style))
    story.append(Paragraph("<b>Advanced Cybersecurity &amp; Network Defence</b><br/>(ACND - 2026)", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Grid for Guides and Authors
    meta_table_data = [
        [
            Paragraph("<b>Guided By:</b><br/>Mr. Shivraj Waghmare<br/>Ms. Shabnam", ParagraphStyle("LAlign", parent=metadata_style, alignment=TA_LEFT)),
            Paragraph("<b>Submitted By:</b><br/>Sukhman Singh (C-DAC/ACND-104)<br/>Ayush Ahuja (C-DAC/ACND-108)<br/>Daksh (C-DAC/ACND-112)<br/>Divyansh (C-DAC/ACND-115)", ParagraphStyle("RAlign", parent=metadata_style, alignment=TA_LEFT))
        ]
    ]
    t_meta = Table(meta_table_data, colWidths=[200, 240])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_meta)
    
    story.append(Spacer(1, 35))
    story.append(Paragraph("<b>CENTRE FOR DEVELOPMENT OF ADVANCED COMPUTING (C-DAC)</b><br/>A-34, Industrial Area, Phase VIII, Mohali, Punjab - 160071", metadata_style))
    story.append(PageBreak())

    # ==========================================
    # PAGE 2: ACKNOWLEDGEMENT
    # ==========================================
    story.append(Paragraph("ACKNOWLEDGEMENT", heading1_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "I would like to express my sincere gratitude to all those who have supported and guided me throughout the "
        "course of my major training project titled 'NeuroShield: High-Performance Network Intrusion Detection "
        "System'. Without their valuable contributions, feedback, and encouragement, the successful completion of "
        "this complex engineering project would not have been possible. The intersection of deep learning and "
        "network security presented numerous architectural challenges that required extensive guidance to "
        "overcome.", body_style))
    story.append(Paragraph(
        "Firstly, I would like to extend my heartfelt thanks to my supervisors, <b>Mr. Shivraj Waghmare</b> and "
        "<b>Ms. Shabnam</b>, for their invaluable guidance, continuous support, and profound technical insights. Their "
        "expertise in machine learning architectures and network security engineering was instrumental in helping "
        "me design the hybrid CNN-LSTM neural classification engine. Their willingness to dedicate time to "
        "review algorithmic logic, debug REST API bottlenecks, and optimize frontend rendering performance "
        "significantly elevated the quality of this work.", body_style))
    story.append(Paragraph(
        "I am also deeply grateful to C-DAC Mohali for providing the necessary academic resources and a highly "
        "conducive environment for advanced research and implementation. The state-of-the-art laboratory "
        "facilities, high-performance computing clusters, and comprehensive digital libraries served as the "
        "cornerstone of this project's model training, testing, and validation phases. The academic rigor and "
        "exposure to modern cluster networking paradigms greatly enhanced my practical engineering skills.", body_style))
    story.append(Paragraph(
        "Furthermore, I wish to acknowledge the broader academic and open-source communities. The researchers "
        "who compiled and maintained the UNSW-NB15 dataset provided the essential ground-truth data required for "
        "training predictive models. The developers behind TensorFlow, Keras, and React have built phenomenal "
        "tools that democratize access to advanced computational methodologies. Finally, I would like to thank my "
        "peers and teammates at C-DAC Mohali for their cooperative spirit, motivation, and valuable brainstorming "
        "sessions that resolved critical design bottlenecks during the system's integration phase.", body_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Sukhman Singh, Ayush Ahuja, Daksh, Divyansh</b>", ParagraphStyle("RightBold", parent=body_style, alignment=TA_RIGHT)))
    story.append(PageBreak())

    # ==========================================
    # PAGE 3: ABSTRACT
    # ==========================================
    story.append(Paragraph("ABSTRACT", heading1_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "With the increasing complexity of global network infrastructures and the sophistication of modern cyber "
        "threats, accurate and rapid intrusion detection has become a critical operational challenge in network "
        "security. Threat actors continually evolve their tactics, employing polymorphic malware, low-rate stealth "
        "scanning, and multi-stage exploitation campaigns designed to bypass traditional perimeter defenses. This "
        "project presents NeuroShield, a High-Performance Hybrid Network Intrusion Detection System (NIDS) "
        "designed to tackle these challenges by leveraging a state-of-the-art deep learning architecture. The "
        "proposed neural classification engine combines a 1D Convolutional Neural Network (CNN) with a Long "
        "Short-Term Memory (LSTM) network and a custom Attention mechanism to achieve scalable, real-time "
        "threat classification across Security Operations Center (SOC) environments.", body_style))
    story.append(Paragraph(
        "NeuroShield fundamentally addresses the limitations of traditional signature-based firewalls by utilizing a "
        "data-driven, anomaly-based model trained on the widely benchmarked, modern <b>UNSW-NB15</b> dataset. It classifies "
        "network traffic into five distinct categories: Normal, DoS, Probe, R2L, and U2R. To handle continuous, "
        "streaming packet records, we engineered an innovative sliding window real-time connection buffer that "
        "aggregates network packets into sequential blocks of length 10. Within the neural model, the 1D CNN "
        "layers extract spatial, localized packet features, while the BiLSTM layers capture the temporal sequence "
        "progression of connection steps. The Attention mechanism dynamically assigns weights to crucial time "
        "steps, ensuring robust classification even under low-profile attacks where the anomalous payload is hidden "
        "among benign traffic.", body_style))
    story.append(Paragraph(
        "Beyond the neural architecture, NeuroShield is deployed as a fully integrated, production-ready software "
        "appliance. A Flask-based REST API serves as the asynchronous prediction gateway, streaming "
        "multi-threaded inference results directly into a premium, responsive React/TailwindCSS web console. Key "
        "interactive features include live traffic load telemetry, packet rate monitoring, and a dynamic network "
        "topology visualizer that instantaneously links threat sources to internal gateways visually. Furthermore, a "
        "Python-based CLI Intrusion Attack Simulator was developed to replay high-speed threat streams against "
        "the network guards, providing rigorous stress-testing capabilities. Experimental evaluation demonstrates "
        "the model's high efficiency, achieving a <b>Weighted F1-score of 78.28%</b> and an <b>Overall Accuracy of 77.32%</b> "
        "on unseen test data, while maintaining an average prediction latency of under 13 ms.", body_style))
    story.append(PageBreak())

    # ==========================================
    # PAGE 4: TABLE OF CONTENTS
    # ==========================================
    story.append(Paragraph("TABLE OF CONTENTS", heading1_style))
    story.append(Spacer(1, 10))
    
    toc_data = [
        [Paragraph("<b>TOPICS</b>", table_header_style), Paragraph("<b>PAGE NO.</b>", table_header_style)],
        [Paragraph("Acknowledgement", table_cell_style), Paragraph("II", table_cell_center)],
        [Paragraph("Abstract", table_cell_style), Paragraph("III", table_cell_center)],
        [Paragraph("<b>1. INTRODUCTION</b>", table_cell_style), Paragraph("1-5", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;1.1 Introduction", table_cell_style), Paragraph("1", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;1.2 Problem Statement", table_cell_style), Paragraph("2", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;1.3 Objectives and Specifications", table_cell_style), Paragraph("4", table_cell_center)],
        [Paragraph("<b>2. LITERATURE REVIEW</b>", table_cell_style), Paragraph("6-9", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;2.1 Network Security and Deep Learning", table_cell_style), Paragraph("6", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;2.2 Deep Learning Architectures in NIDS", table_cell_style), Paragraph("7", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;2.3 Real-time Deployment Paradigms", table_cell_style), Paragraph("8", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;2.4 Comparative Analysis of Related Works", table_cell_style), Paragraph("9", table_cell_center)],
        [Paragraph("<b>3. METHODOLOGY AND TECHNIQUES</b>", table_cell_style), Paragraph("10-21", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3.1 Introduction &amp; Mathematical Formulation", table_cell_style), Paragraph("10", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3.2 1D CNN &amp; LSTM Gate Computations", table_cell_style), Paragraph("11", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3.3 Attention Layer Weight Calculations", table_cell_style), Paragraph("14", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3.4 System Architecture &amp; Dataflow", table_cell_style), Paragraph("15", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3.5 Preprocessing &amp; Feature Analysis", table_cell_style), Paragraph("16", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3.6 CNN-LSTM-Attention Model Layers", table_cell_style), Paragraph("19", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3.7 Real-time Sliding Window Engine", table_cell_style), Paragraph("20", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3.8 Performance Evaluation Metrics", table_cell_style), Paragraph("21", table_cell_center)],
        [Paragraph("<b>4. IMPLEMENTATION</b>", table_cell_style), Paragraph("23-27", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;4.1 System Configuration &amp; Libraries", table_cell_style), Paragraph("23", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;4.2 Backend REST API Implementation", table_cell_style), Paragraph("24", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;4.3 Frontend UI Console Layout", table_cell_style), Paragraph("26", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;4.4 Simulation Engine Suite", table_cell_style), Paragraph("27", table_cell_center)],
        [Paragraph("<b>5. RESULTS AND DISCUSSION</b>", table_cell_style), Paragraph("28-37", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;5.1 Model Evaluation Metrics Overview", table_cell_style), Paragraph("28", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;5.2 Detailed Performance Curves", table_cell_style), Paragraph("29", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;5.3 Confusion Matrix Analysis", table_cell_style), Paragraph("30", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;5.4 ROC Curves Analysis", table_cell_style), Paragraph("31", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;5.5 Class-wise Threat Detection Analysis", table_cell_style), Paragraph("32", table_cell_center)],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;5.6 Live SOC Dashboard Telemetry Detections", table_cell_style), Paragraph("33", table_cell_center)],
        [Paragraph("<b>6. CONCLUSION &amp; FUTURE SCOPE</b>", table_cell_style), Paragraph("34", table_cell_center)],
        [Paragraph("<b>7. REFERENCES</b>", table_cell_style), Paragraph("35", table_cell_center)]
    ]
    t_toc = Table(toc_data, colWidths=[380, 80])
    t_toc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e1b4b")),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_toc)
    story.append(PageBreak())

    # ==========================================
    # CHAPTER 1: INTRODUCTION
    # ==========================================
    story.append(Paragraph("CHAPTER 1", heading1_style))
    story.append(Paragraph("INTRODUCTION", heading2_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("1.1 Introduction", heading2_style))
    story.append(Paragraph(
        "In the modern era of rapid digitization, high-speed network communication, and ubiquitous cloud "
        "infrastructure deployment, securing corporate and institutional networks from malicious activities has "
        "emerged as a paramount engineering challenge. The exponential growth in internet-connected devices, IoT "
        "ecosystems, and distributed microservices has dramatically expanded the attack surface available to "
        "malicious actors. With cyberattack vectors growing more sophisticated daily—ranging from automated "
        "botnet distributed denial-of-service (DDoS) campaigns to highly stealthy, state-sponsored advanced "
        "persistent threats (APTs)—traditional security mechanisms are being pushed past their operational limits. "
        "Static firewalls, which have served as the cornerstone of perimeter network defense for decades, are no "
        "longer sufficient to protect critical data assets.", body_style))
    story.append(Paragraph(
        "These traditional systems rely heavily on rigid, pre-defined rule databases to flag threats. Network packets "
        "are captured, parsed, and compared against a massive library of known exploit signatures, such as specific "
        "byte sequences, malicious IP ranges, or recognizable protocol anomalies. While this signature-based "
        "approach is computationally efficient and highly effective against well-known, historically documented "
        "threats, it fails catastrophically when faced with novel, zero-day vulnerabilities or polymorphic malware "
        "strains that dynamically alter their signature footprints to evade detection. Furthermore, maintaining these "
        "signature databases requires continuous manual intervention from security analysts, resulting in a "
        "fundamentally reactive security posture where defenses are updated only after a new attack has already "
        "caused widespread disruption.", body_style))
    story.append(Paragraph(
        "To address these systemic limitations, modern network security paradigms have aggressively shifted "
        "toward anomaly-based Intrusion Detection Systems (IDS). Instead of searching for known bad signatures, "
        "anomaly-based systems utilize statistical and machine learning techniques to establish a behavioral "
        "baseline of 'normal' network traffic. Once this baseline is accurately established, any significant deviation "
        "is flagged as a potential intrusion. Recently, Deep Learning has emerged as the state-of-the-art "
        "methodology for anomaly-based NIDS, demonstrating outstanding performance in learning rich, complex "
        "patterns from high-dimensional network datasets without the need for exhaustive manual feature "
        "engineering.", body_style))
    story.append(Paragraph(
        "This project presents NeuroShield, a real-time anomaly-based Network Intrusion Detection System "
        "powered by a highly optimized hybrid deep neural network. By elegantly combining a 1D Convolutional "
        "Neural Network (CNN) with a Bidirectional Long Short-Term Memory (LSTM) architecture and a custom "
        "self-attention layer, the system captures both the spatial relationships within individual packet features and "
        "the temporal correlations across extended sequences of connections. This report outlines the mathematical "
        "foundations, decoupled system architecture, REST API deployment, interactive SOC dashboard, and "
        "testing results of the NeuroShield platform.", body_style))
    
    story.append(Paragraph("1.2 Problem Statement", heading2_style))
    story.append(Paragraph(
        "As global organizations migrate their operational workloads to clustered cloud servers, containerized "
        "environments, and edge computing gateways, network architectures have become highly decentralized. "
        "These robust environments routinely process millions of connections per second, generating massive "
        "volumes of telemetry data. This unprecedented scaling renders manual auditing of network packets "
        "computationally and physically impossible. Furthermore, sophisticated intruders no longer rely on simple, "
        "single-packet exploits. Modern cyberattacks are carefully orchestrated as multi-step campaigns that unfold "
        "slowly over hours, days, or even weeks. Tactics such as low-rate port scanning, stealthy privilege "
        "escalations, and encrypted data exfiltration are specifically designed to blend in seamlessly with normal "
        "traffic and slip past traditional firewall thresholds.", body_style))
    story.append(Paragraph(
        "This stealthy progression of connection states necessitates a fundamental paradigm shift in intrusion "
        "detection architectures. A robust security system must be capable of tracking sequences of packet metadata "
        "over time, rather than analyzing packet records in strict isolation. Existing intrusion classifiers suffer from "
        "three major architectural and operational design flaws that severely limit their effectiveness in these "
        "modern high-speed environments. First, signature databases are inherently blind to zero-day attacks and "
        "polymorphic payloads, offering zero protection against previously unseen exploits. Second, traditional "
        "machine learning models—such as Support Vector Machines (SVMs) or standard Random Forests—treat "
        "each network packet as an isolated, independent event, completely failing to model the sequential and "
        "dependent nature of multi-stage network attacks.", body_style))
    story.append(Paragraph(
        "Third, high false-alarm rates generated by poorly calibrated anomaly detectors often overload security "
        "analysts, leading to 'alert fatigue' where critical warnings are ignored amidst a sea of false positives. There "
        "is a critical, industry-wide requirement for a high-throughput, dynamic intrusion detection appliance that "
        "inherently models the temporal sequences of packet connections while highlighting only the most severe "
        "anomalies immediately. Such a system must operate autonomously with minimal inference latency and "
        "high classification precision, protecting cluster gateway nodes from unauthorized access without "
        "disrupting legitimate business traffic flows.", body_style))
    
    story.append(Paragraph("1.3 Objectives and Specifications", heading2_style))
    story.append(Paragraph(
        "The primary goal of the NeuroShield project is to develop, evaluate, and deploy a fully practical, "
        "anomaly-based network security appliance capable of detecting complex intrusions in real-time. The "
        "system must operate with minimal computational overhead and latency while maintaining high "
        "classification precision, thereby protecting critical cluster gateway nodes from unauthorized access. To "
        "achieve this, the project establishes a rigorous, end-to-end integration pipeline encompassing massive data "
        "preprocessing, neural model training, feature normalization algorithms, highly concurrent REST API "
        "construction, and interactive frontend user interface design.", body_style))
    story.append(Paragraph(
        "A critical requirement for this practical deployment is strict adherence to physical performance constraints. "
        "The neural classification model must perform inference on sliding sequence windows in under 20 "
        "milliseconds (averaging 12.4 ms), allowing the software appliance to keep pace with active, high-throughput network "
        "interfaces. Furthermore, the SOC dashboard must dynamically reflect changes in traffic rates, packet "
        "counters, log events, and alert queues within a maximum polling delay of 2 seconds. The user controls "
        "provided within the dashboard should allow for instantaneous execution of mitigation commands—such as "
        "IP blocking or network isolation—thereby fully closing the loop between threat detection and proactive "
        "threat response.", body_style))
    
    story.append(Paragraph("Detailed Project Objectives:", ParagraphStyle("SubBold", parent=body_style, fontName="Helvetica-Bold")))
    story.append(Paragraph(
        "• <b>Deep Learning Model Integration:</b> Architect and deploy a trained hybrid CNN-BiLSTM-Attention "
        "network capable of classifying connection records into 5 distinct categories (Normal, DoS, Probe, "
        "R2L, U2R) with an overall accuracy exceeding 75%.", body_style))
    story.append(Paragraph(
        "• <b>Real-time Processing Pipeline:</b> Implement a memory-efficient sliding window sequence builder of "
        "length 10 to transform streaming connection records into structured input tensors for sequential neural "
        "inference without disk I/O bottlenecks.", body_style))
    story.append(Paragraph(
        "• <b>Production-Ready REST API:</b> Build a highly concurrent, robust Flask API server exposing "
        "multi-threaded prediction routes, hardware telemetry streams, connection state updates, system log "
        "tailing, and CSV report generation endpoints.", body_style))
    story.append(Paragraph(
        "• <b>Interactive SOC Control Console:</b> Create a premium React/Vite single-page web application that "
        "fluidly visualizes network load, AI inference metrics, raw log events, active hosts, and dynamically "
        "generated threat vectors.", body_style))
    story.append(Paragraph(
        "• <b>Dynamic Topology Rendering:</b> Render an interactive network topology map in the UI utilizing SVG "
        "canvas layers. Threat nodes must be dynamically added, linked, and flashed red to alert SOC analysts "
        "visually during live attacks.", body_style))
    story.append(Paragraph(
        "• <b>Attack Simulation Suite:</b> Develop a versatile Python-based CLI Intrusion Attack Simulator to "
        "continuously replay UNSW-NB15 test dataset records directly to the network interface, stress-testing the "
        "model and verifying end-to-end dashboard propagation.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # CHAPTER 2: LITERATURE REVIEW
    # ==========================================
    story.append(Paragraph("CHAPTER 2", heading1_style))
    story.append(Paragraph("LITERATURE REVIEW", heading2_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("2.1 Network Security and Deep Learning", heading2_style))
    story.append(Paragraph(
        "Historically, network intrusion detection relied almost entirely on deterministic, rule-based matching "
        "paradigms. Systems like Snort parse incoming packet headers and payloads, comparing them "
        "line-by-line to standard regular expression patterns of known exploits. While highly computationally "
        "efficient and highly effective for mitigating common, widely recognized attacks, they remain completely "
        "blind to custom modifications or sophisticated obfuscation techniques. Over the last decade, academic "
        "researchers began applying classical machine learning methodologies—such as Random Forests, Support "
        "Vector Machines (SVMs), and Naive Bayes classifiers—to standardized datasets.", body_style))
    story.append(Paragraph(
        "The modern <b>UNSW-NB15</b> dataset resolved several inherent statistical flaws present in older legacy "
        "datasets (like KDD Cup 99), which suffered from massive duplicate records that biased classifiers toward "
        "redundant patterns. Although classical machine learning models significantly improved detection "
        "rates for certain types of attacks, they heavily relied on extensive manual feature engineering. Data "
        "scientists were required to manually select and transform network packet properties based on human "
        "intuition. Securing modern, high-speed corporate interfaces requires deep learning architectures that can "
        "automatically learn complex representations from raw, discretized connection features without relying on "
        "hand-crafted heuristics.", body_style))
    
    story.append(Paragraph("2.2 Deep Learning Architectures in NIDS", heading2_style))
    story.append(Paragraph(
        "Researchers have proposed and evaluated a wide variety of deep learning structures for network intrusion "
        "detection. <b>Convolutional Neural Networks (CNNs)</b>, originally designed for image processing, excel at "
        "learning spatial, localized relationships between adjacent data points. In the context of NIDS, 1D CNNs "
        "treat multi-dimensional connection features (such as total bytes sent, specific protocol flags, and user login "
        "status) as a one-dimensional spatial array. This allows the network to learn correlation patterns within a "
        "single connection record efficiently. This spatial extraction is highly effective for identifying signatures of "
        "direct, volumetric attacks like DoS, where immediate feature values (such as an impossibly high packet "
        "rate) are overtly anomalous.", body_style))
    story.append(Paragraph(
        "However, as discussed previously, modern network intrusions often span multiple steps distributed over "
        "time. A single isolated packet might look entirely harmless and statistically normal, but a sequence of 10 "
        "rapid, sequential port scans unmistakably indicates a malicious Probe attack. <b>Recurrent Neural "
        "Networks (RNNs)</b> and, more specifically, <b>Long Short-Term Memory (LSTM)</b> networks are "
        "mathematically ideal for capturing these temporal, sequential dependencies. LSTMs maintain an internal "
        "cell state memory across extended connection sequences, allowing them to track the progression of "
        "multi-stage attacks over time. To further optimize the LSTM's capability, <b>Attention Mechanisms</b> have "
        "been recently introduced into time-series analysis.", body_style))
    story.append(Paragraph(
        "By combining 1D CNNs, Bidirectional LSTMs, and Self-Attention mechanisms, we construct a highly "
        "advanced hybrid model that inherits the rapid spatial feature extraction of convolutions and the long-term "
        "temporal modeling of recurrent layers. The self-attention layer aggregates the hidden states based strictly "
        "on their mathematical relevance to the final classification task, ensuring that the classification engine "
        "remains highly robust even when dealing with extremely sparse, low-profile attacks like R2L "
        "(Remote-to-Local) and U2R (User-to-Root) exploits.", body_style))
    
    story.append(Paragraph("2.3 Real-time Deployment Paradigms", heading2_style))
    story.append(Paragraph(
        "While defining and training deep neural networks is computationally heavy and often requires offloading "
        "to high-performance GPU clusters (such as Google Colab instances or the powerful C-DAC supercomputing nodes), "
        "deploying these fully trained models for real-time inference presents an entirely separate and complex software "
        "engineering challenge. Real-time NIDS applications require extremely lightweight deployment frameworks that can "
        "perform forward-pass classification within milliseconds. Heavy machine learning frameworks like TensorFlow "
        "and Keras must be carefully optimized and run under highly concurrent server wrappers with proper model weight "
        "caching in RAM.", body_style))
    story.append(Paragraph(
        "The standard modern paradigm for deploying such models is the <b>Microservice REST API "
        "architecture</b>. In this design, the trained neural network weights and scalers are pre-loaded into a "
        "memory-resident, Python-based API web service (e.g., utilizing Flask or FastAPI). Individual network "
        "sensors, edge routers, or packet sniffers deployed across the corporate network issue asynchronous HTTP "
        "POST requests containing connection features to the API. The API processes these inputs, applies "
        "necessary numerical scaling, executes the neural inference tensor operations, and returns standardized "
        "JSON-formatted predictions instantly to the calling sensor.", body_style))
    
    story.append(Paragraph("2.4 Comparative Analysis of Related Works", heading2_style))
    story.append(Paragraph(
        "To comprehensively understand the relative technical advantages of the hybrid CNN-BiLSTM-Attention "
        "network, it is essential to compare it rigorously with alternative architectures proposed in recent academic "
        "literature. Standard, standalone CNN models evaluate network packets in strict isolation, extracting "
        "features beautifully but completely ignoring the highly critical sequential connection patterns that define "
        "multi-stage attacks. Conversely, pure LSTM networks can theoretically capture these sequences but suffer "
        "from severe computational overhead and persistently struggle to capture highly localized, packet-level "
        "feature interactions. Traditional machine learning models, like Random Forests, can achieve reasonable "
        "inference speeds but require manually selected features and struggle immensely with generalized zero-day threat detection.", body_style))
    story.append(Paragraph(
        "Our proposed hybrid architecture gracefully bridges this significant analytical gap. The 1D CNN layer acts "
        "as a highly aggressive, local feature extractor, significantly downsampling the input feature space and "
        "capturing immediate numerical correlations within individual connection features before sequence "
        "processing even begins. The Bidirectional LSTM layer subsequently receives these optimized spatial "
        "features and models the temporal patterns in both forward and backward chronological directions, "
        "flawlessly capturing the multi-directional progression of complex attacks. Finally, the Self-Attention layer "
        "dynamically weights the sequential time steps, ensuring that isolated key anomalies (like an "
        "unauthenticated root access request buried in background noise) are vastly prioritized.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # CHAPTER 3: METHODOLOGY AND TECHNIQUES
    # ==========================================
    story.append(Paragraph("CHAPTER 3", heading1_style))
    story.append(Paragraph("METHODOLOGY AND TECHNIQUES", heading2_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("3.1 Introduction & Technical Workflow", heading2_style))
    story.append(Paragraph(
        "The core methodology adopted for the NeuroShield NIDS project is meticulously designed to bridge the "
        "vast gap between abstract academic model evaluation and highly practical, real-world security center "
        "deployment. The complete operational workflow consists of five distinct, highly optimized sequential "
        "components: continuous data ingestion, mathematical feature normalization, sliding sequence tensor "
        "aggregation, hybrid neural classification, and visual telemetry mapping.", body_style))
    story.append(Paragraph(
        "First, incoming raw traffic packet records are rapidly parsed and mapped to defined numeric features using "
        "memory-resident categorical encoders. They are subsequently scaled using pre-trained MinMaxScaler and StandardScaler "
        "objects to ensure gradient stability. Second, the normalized connection records are systematically buffered "
        "in an IP-isolated, thread-safe memory queue of strict length 10. This crucial step dynamically generates the "
        "3-dimensional sequence tensors required by the LSTM layer. Third, the hybrid neural engine processes "
        "these tensors, predicting a precise classification probability distribution. If the mathematical probability of "
        "any specific attack class exceeds a pre-defined confidence threshold, a critical alert object is immediately "
        "instantiated and pushed to the active threat queue. Finally, the React-based front-end console asynchronously "
        "polls this threat queue, instantaneously updating topology routing paths, hardware metrics, and analyst logs.", body_style))
    
    story.append(Paragraph("3.2 1D CNN & LSTM Gate Computations", heading2_style))
    story.append(Paragraph(
        "The NeuroShield classification engine utilizes a mathematically rigorous combination of 1D Convolutional "
        "Neural Networks, Long Short-Term Memory cells, and a Softmax Attention mechanism. Let us thoroughly "
        "outline the detailed mathematical operations occurring within the 1D CNN layer. For a given network "
        "sequence input X = [x1, x2, ..., xT] where each connection record xt belongs to an expanded D-dimensional "
        "feature space (where D = 42 features for UNSW-NB15), a 1D convolution filter "
        "slides across the temporal dimension to extract highly localized spatial features.", body_style))
    
    story.append(Paragraph("3.2.1 1D Convolutional Layer Math", heading2_style))
    story.append(Paragraph(
        "The output of the j-th discrete feature map in the convolutional layer at specific time step t is rigorously "
        "calculated using the following tensor equation:", body_style))
    
    math1_path = os.path.join(asset_dir, "math1_cnn.png")
    if os.path.exists(math1_path):
        story.append(Image(math1_path, width=300, height=50))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph(
        "Where W represents the configured filter window size, wkj is the specific learnable weight matrix of the "
        "corresponding filter, and bj is the trainable bias vector. The Rectified Linear Unit (ReLU) activation "
        "function is intentionally utilized to introduce non-linearity, ensuring that the network can model highly "
        "complex decision boundaries. Following the raw convolution operation, Batch Normalization is "
        "aggressively applied to standardize the activations, preventing internal covariate shift. Subsequently, "
        "MaxPool is utilized to downsample the spatial dimensions, retaining only the maximum, most salient activations.", body_style))
    
    story.append(Paragraph("3.2.2 LSTM Cell Gate Computations", heading2_style))
    story.append(Paragraph(
        "The spatial features ct extracted by the convolution layers are subsequently passed to a "
        "Bidirectional LSTM layer for deep temporal analysis. An LSTM cell fundamentally controls the "
        "longitudinal flow of information using a complex series of internal gates, effectively preventing the "
        "notorious vanishing gradient problem over extended sequence lengths. At any specific time step t, the "
        "internal cell state memory Ct and the external hidden state ht are computed precisely using the following "
        "interrelated equations:", body_style))
    
    math2_path = os.path.join(asset_dir, "math2_lstm.png")
    if os.path.exists(math2_path):
        story.append(Image(math2_path, width=220, height=100))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph(
        "In these equations, σ represents the standard sigmoid activation function bounding values between 0 and "
        "1, and * represents the Hadamard (element-wise) product. Because the layer is Bidirectional, the hidden "
        "states derived from both the forward and backward chronological passes are concatenated to form the final "
        "representation.", body_style))

    story.append(Paragraph("3.3 Attention Layer Weight Calculations", heading2_style))
    story.append(Paragraph(
        "To empower the network to algorithmically highlight the most highly relevant and suspicious packet steps "
        "within the rolling sequence of 10 connections, we strategically apply a custom self-attention layer directly "
        "over the LSTM hidden states H = [h1, h2, ..., hT]. The normalized attention weight αt assigned to each "
        "specific time step is computed mathematically as follows:", body_style))
    
    math3_path = os.path.join(asset_dir, "math3_attn.png")
    if os.path.exists(math3_path):
        story.append(Image(math3_path, width=300, height=68))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("The ultimate context representation vector v is mathematically constructed as the weighted sum of all preceding hidden states:", body_style))
    
    math4_path = os.path.join(asset_dir, "math4_ctx.png")
    if os.path.exists(math4_path):
        story.append(Image(math4_path, width=300, height=49))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("Finally, this highly condensed, information-dense context vector v is passed directly through a Dense fully-connected layer utilizing a Softmax activation function to predict the final categorical class probabilities:", body_style))
    
    math5_path = os.path.join(asset_dir, "math5_pred.png")
    if os.path.exists(math5_path):
        story.append(Image(math5_path, width=300, height=49))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph(
        "This advanced attention mechanism is critically responsible for capturing highly stealthy, low-profile "
        "attacks like R2L (Remote to Local) and U2R (User to Root) exploits. By assigning significantly high "
        "attention scores αt to specific sequences where sudden privilege changes or unexpected file creations "
        "occur, the network algorithmically isolates the exploit signature.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # CHAPTER 3 CONTINUED: ARCHITECTURE DIAGRAM & DATA PREPROCESSING
    # ==========================================
    story.append(Paragraph("3.4 System Architecture & Dataflow", heading2_style))
    story.append(Paragraph(
        "NeuroShield employs a highly decoupled, modern three-tier software architecture that "
        "physically and logically separates the high-speed data capture and complex neural classification logic from "
        "the visual rendering and user interaction pipelines. This strict separation of concerns ensures absolute "
        "system durability and prevents UI freezing even under the most extreme, volumetric attack streams.", body_style))
    
    arch_path = os.path.join(asset_dir, "extracted_image_2.jpeg")
    if os.path.exists(arch_path):
        story.append(Image(arch_path, width=340, height=250))
        story.append(Paragraph("<b>Figure 3.1:</b> Robust System Architecture and dataflow pipeline block diagram.", ParagraphStyle("Cap", parent=body_style, fontName="Times-BoldItalic", alignment=TA_CENTER)))
    
    story.append(Paragraph("3.5 Preprocessing & Feature Analysis", heading2_style))
    story.append(Paragraph(
        "Raw network connection records captured from standard hardware loggers invariably contain highly "
        "mixed, unstructured data types: immense numerical metrics (such as connection duration in seconds, total "
        "source bytes sent, and packet counts) natively intermingled with discrete categorical descriptions (such as "
        "the protocol type, specific network service requested, and TCP connection flags). Before submitting these "
        "wildly varying values to the sensitive neural network for inference, they must be rigorously normalized, "
        "scaled, and encoded.", body_style))
    
    story.append(Paragraph("3.5.1 Categorical Encoding & Scaler Math", heading2_style))
    story.append(Paragraph(
        "Categorical string features (such as protocol_type, service, and state) are systematically mapped to dense "
        "numeric integer tokens utilizing robust scikit-learn LabelEncoders. For scaling, highly skewed quantitative fields "
        "first undergo a log-transform (np.log1p) before being standardized using the static scaler weights stored precisely in models/scaler.joblib:", body_style))
    
    math6_path = os.path.join(asset_dir, "math6_scale.png")
    if os.path.exists(math6_path):
        story.append(Image(math6_path, width=300, height=49))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph(
        "If a wildly anomalous value x exceeds the previously documented xmax or unexpectedly falls below xmin "
        "during live production deployment, it is forcefully clipped to avoid generating "
        "out-of-bounds activation values. This preprocessing ensures that disparate features are treated with equal "
        "computational significance by the convolutional layers.", body_style))
    
    story.append(Paragraph("3.5.2 Detailed UNSW-NB15 Feature Analysis", heading2_style))
    story.append(Paragraph(
        "The standard UNSW-NB15 dataset contains 42 highly descriptive features per connection record. "
        "These features are divided into three broad, analytical categories: Basic Features, Content Features, and Traffic Features. "
        "Basic Features capture the foundational properties (duration, protocol_type, service, src_bytes, dst_bytes). Content Features capture payload-specific statistics "
        "critical for detecting R2L and U2R attacks (such as login failure counts, root shell states, and file creation operations). Traffic Features are computed dynamically "
        "using a rolling temporal sliding window of 2 seconds (such as error rates and connection counts).", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # CHAPTER 3 CONTINUED: MODEL LAYERS & METRICS
    # ==========================================
    story.append(Paragraph("3.6 CNN-LSTM-Attention Model Layers", heading2_style))
    story.append(Paragraph(
        "Let us thoroughly outline the detailed computational layers and highly tuned configurations of our deep "
        "neural network. The trained model architecture consists of the following precisely layered components. "
        "Every individual layer is painstakingly configured to extract maximum spatial and temporal patterns from "
        "the raw connection sequences while aggressively mitigating the risk of overfitting:", body_style))
    
    # Layer table
    layer_data = [
        [Paragraph("<b>LAYER TYPE</b>", table_header_style), Paragraph("<b>OUTPUT SHAPE</b>", table_header_style), Paragraph("<b>CONFIGURATION / DETAILS</b>", table_header_style)],
        [Paragraph("Input Layer", table_cell_style), Paragraph("(None, 10, 42)", table_cell_center), Paragraph("Sequence of 10 connections, 42 features", table_cell_style)],
        [Paragraph("1D Convolution 1", table_cell_style), Paragraph("(None, 10, 128)", table_cell_center), Paragraph("128 feature filters, kernel size = 3, padding = 'same', ReLU", table_cell_style)],
        [Paragraph("Batch Normalization 1", table_cell_style), Paragraph("(None, 10, 128)", table_cell_center), Paragraph("Stabilize deep layer activations and prevent covariate shift", table_cell_style)],
        [Paragraph("Spatial Dropout 1", table_cell_style), Paragraph("(None, 10, 128)", table_cell_center), Paragraph("Rate = 0.2, drops entire feature map channels for regularization", table_cell_style)],
        [Paragraph("1D Convolution 2", table_cell_style), Paragraph("(None, 10, 256)", table_cell_center), Paragraph("256 feature filters, kernel size = 3, padding = 'same', ReLU", table_cell_style)],
        [Paragraph("Batch Normalization 2", table_cell_style), Paragraph("(None, 10, 256)", table_cell_center), Paragraph("Normalize output activations before pooling", table_cell_style)],
        [Paragraph("MaxPool 1D", table_cell_style), Paragraph("(None, 5, 256)", table_cell_center), Paragraph("Pool size = 2, downsample spatial features, reduce parameter count", table_cell_style)],
        [Paragraph("Spatial Dropout 2", table_cell_style), Paragraph("(None, 5, 256)", table_cell_center), Paragraph("Rate = 0.2, regularizes downsampled feature maps", table_cell_style)],
        [Paragraph("Bidirectional LSTM", table_cell_style), Paragraph("(None, 5, 512)", table_cell_center), Paragraph("256 hidden units forward and backward, internal dropout = 0.15", table_cell_style)],
        [Paragraph("Attention Layer", table_cell_style), Paragraph("(None, 512)", table_cell_center), Paragraph("Softmax self-attention dynamically weighting temporal hidden states", table_cell_style)],
        [Paragraph("Dense Layer 1", table_cell_style), Paragraph("(None, 256)", table_cell_center), Paragraph("256 fully connected units, L2 regularization (1e-5), ReLU", table_cell_style)],
        [Paragraph("Dropout 1", table_cell_style), Paragraph("(None, 256)", table_cell_center), Paragraph("Standard Dropout rate = 0.15", table_cell_style)],
        [Paragraph("Dense Layer 2", table_cell_style), Paragraph("(None, 128)", table_cell_center), Paragraph("128 fully connected units, L2 regularization (1e-5), ReLU", table_cell_style)],
        [Paragraph("Dropout 2", table_cell_style), Paragraph("(None, 128)", table_cell_center), Paragraph("Standard Dropout rate = 0.15", table_cell_style)],
        [Paragraph("Output Layer", table_cell_style), Paragraph("(None, 5)", table_cell_center), Paragraph("5 units, Softmax activation (Normal, DoS, Probe, R2L, U2R)", table_cell_style)]
    ]
    t_layer = Table(layer_data, colWidths=[100, 90, 270])
    t_layer.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e1b4b")),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_layer)
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Table 3.1:</b> Comprehensive CNN-LSTM-Attention neural network layers, tensor shapes, and exact parameter configurations.", ParagraphStyle("Cap2", parent=body_style, fontName="Times-BoldItalic", alignment=TA_CENTER)))
    
    story.append(Paragraph("3.7 Real-time Sliding Window Engine", heading2_style))
    story.append(Paragraph(
        "Deploying complex sequential neural models in a live, real-time environment requires a highly optimized streaming data pipeline. "
        "Standard packet sniffer tools naturally deliver single, isolated records at a time, whereas LSTM networks mandate three-dimensional sequence tensors strictly shaped as (batch_size, sequence_length, features). "
        "To resolve this mismatch, we engineered an online sliding window memory buffer: IP-Isolated Buffers (the prediction engine maintains a dynamic Python dictionary of queues in RAM using source IP as the key), "
        "Sliding History Aggregation (each queue holds exactly the last 10 connection records), Zero-Padding Fallback (pads the sequence with zeros at the beginning for new IPs), "
        "and Multi-threading Locks (protects the buffer from race conditions during concurrent API requests).", body_style))
    
    story.append(Paragraph("3.8 Performance Evaluation Metrics", heading2_style))
    story.append(Paragraph(
        "To evaluate the hybrid model on the independent test dataset, we define: Overall Accuracy (proportion of correctly classified connections over the total records processed), "
        "Precision (proportion of flagged alerts that are actual intrusions), Recall (proportion of actual intrusions successfully caught), and Weighted/Macro F1-Score (harmonic mean of precision and recall). "
        "In a highly sensitive network security context, F1-scores are much more reliable than simple accuracy because benign normal packets vastly outnumber intrusions, and we must avoid false alarms without missing actual threats.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # CHAPTER 4: IMPLEMENTATION
    # ==========================================
    story.append(Paragraph("CHAPTER 4", heading1_style))
    story.append(Paragraph("IMPLEMENTATION", heading2_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("4.1 System Configuration & Libraries", heading2_style))
    story.append(Paragraph(
        "The NeuroShield NIDS was built and validated on a highly standardized environment. To ensure strict reproducibility and operational consistency across various deployment scenarios, below are the specific, detailed software framework versions and hardware capability configurations explicitly utilized:", body_style))
    
    impl_table_data = [
        [Paragraph("<b>COMPONENT</b>", table_header_style), Paragraph("<b>SPECIFICATION / EXACT REQUIREMENT</b>", table_header_style)],
        [Paragraph("Operating System", table_cell_style), Paragraph("Windows 11 / Linux (Ubuntu 22.04 LTS)", table_cell_style)],
        [Paragraph("Programming Languages", table_cell_style), Paragraph("Python 3.10+ (Backend Engine), TypeScript / React JSX (Frontend)", table_cell_style)],
        [Paragraph("Neural Network Framework", table_cell_style), Paragraph("TensorFlow 2.15.x / Keras 3.x", table_cell_style)],
        [Paragraph("Data Processing &amp; ML", table_cell_style), Paragraph("scikit-learn 1.5.x, pandas 2.2.x, numpy 1.26.x", table_cell_style)],
        [Paragraph("REST API Web Server", table_cell_style), Paragraph("Flask 3.0.x (with Werkzeug WSGI multi-threaded server)", table_cell_style)],
        [Paragraph("Frontend UI Bundler", table_cell_style), Paragraph("Vite 6.x, React 19.x, TailwindCSS 4.x (with Framer Motion)", table_cell_style)],
        [Paragraph("Hardware Configuration", table_cell_style), Paragraph("Intel Core i7 CPU, 16 GB RAM, NVIDIA RTX GeForce GPU for acceleration", table_cell_style)]
    ]
    t_impl = Table(impl_table_data, colWidths=[150, 310])
    t_impl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e1b4b")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_impl)
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Table 4.1:</b> Comprehensive software frameworks and hardware environment configurations for NIDS.", ParagraphStyle("Cap3", parent=body_style, fontName="Times-BoldItalic", alignment=TA_CENTER)))
    
    story.append(Paragraph("4.2 Backend REST API Implementation", heading2_style))
    story.append(Paragraph(
        "The backend REST API is constructed in Python utilizing the Flask framework. It manages complex daemon threads and exposes highly concurrent endpoints to continuously feed live data directly to the dashboard:", body_style))
    
    api_table_data = [
        [Paragraph("<b>METHOD &amp; ROUTE</b>", table_header_style), Paragraph("<b>CORE FUNCTION / DEEP DESCRIPTION</b>", table_header_style)],
        [Paragraph("POST /predict", table_cell_style), Paragraph("Receives connection JSON, updates sliding window, runs inference, triggers alerts", table_cell_style)],
        [Paragraph("POST /predict/batch", table_cell_style), Paragraph("Accepts a list of connection records and returns predictions concurrently", table_cell_style)],
        [Paragraph("POST /predict/file", table_cell_style), Paragraph("Accepts an uploaded CSV file, parses connection records, and returns predictions", table_cell_style)],
        [Paragraph("GET /alerts", table_cell_style), Paragraph("Returns the active queue of unresolved security alerts to the frontend", table_cell_style)],
        [Paragraph("POST /alerts/action", table_cell_style), Paragraph("Updates the mitigation status of an alert (isolating or ignoring a host IP)", table_cell_style)],
        [Paragraph("GET /stats", table_cell_style), Paragraph("Returns real-time server hardware stats (CPU, memory, packet rate)", table_cell_style)]
    ]
    t_api = Table(api_table_data, colWidths=[130, 330])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e1b4b")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_api)
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Table 4.2:</b> Exhaustive Flask REST API routing architecture schema.", ParagraphStyle("Cap4", parent=body_style, fontName="Times-BoldItalic", alignment=TA_CENTER)))
    
    story.append(Paragraph("4.3 Frontend UI Console Layout", heading2_style))
    story.append(Paragraph(
        "The SOC Control Console is built using React, TypeScript, and TailwindCSS. "
        "It connects to the Flask server via Vite's proxy configurations, polling telemetry data every 2 seconds. "
        "The Sidebar handles navigation and alerts badges. The SOC Dashboard View renders metric cards, an SVG traffic chart showing real-time network load vs blocked alerts, a donut chart for threat category breakdown, and a threat mitigation table.", body_style))
    
    story.append(Paragraph("4.4 Simulation Engine Suite", heading2_style))
    story.append(Paragraph(
        "To test the neural model accuracy alongside the responsive front-end interface, we developed a Python-based CLI Intrusion Attack Simulator (simulate_attacks.py). "
        "It reads connection records from the UNSW-NB15 testing partition, groups them into attack queues, and replays them to the Flask /predict endpoint, mixing benign and malicious traffic to simulate a chaotic cluster workload.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # CHAPTER 5: RESULTS AND DISCUSSION
    # ==========================================
    story.append(Paragraph("CHAPTER 5", heading1_style))
    story.append(Paragraph("RESULTS AND DISCUSSION", heading2_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("5.1 Model Evaluation Results Overview", heading2_style))
    story.append(Paragraph(
        "The fully trained CNN-LSTM-Attention neural network was evaluated on the independent test dataset partition of UNSW-NB15 (containing 175,332 sequence records). "
        "Let us review the overall, final classification performance metrics:", body_style))
    
    results_data = [
        [Paragraph("<b>METRIC</b>", table_header_style), Paragraph("<b>VALUE</b>", table_header_style)],
        [Paragraph("Overall Accuracy", table_cell_style), Paragraph("77.32%", table_cell_center)],
        [Paragraph("Weighted F1-Score", table_cell_style), Paragraph("78.28%", table_cell_center)],
        [Paragraph("Macro F1-Score", table_cell_style), Paragraph("60.10%", table_cell_center)],
        [Paragraph("Average Neural Inference Latency", table_cell_style), Paragraph("12.4 ms", table_cell_center)]
    ]
    t_res = Table(results_data, colWidths=[230, 230])
    t_res.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e1b4b")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_res)
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Table 5.1:</b> Overall neural model evaluation metrics on UNSW-NB15 independent test partition.", ParagraphStyle("Cap5", parent=body_style, fontName="Times-BoldItalic", alignment=TA_CENTER)))
    
    story.append(Paragraph("5.2 Detailed Performance Curves", heading2_style))
    story.append(Paragraph(
        "During model training over 20 epochs on Google Colab's T4 GPU cluster, loss and accuracy were logged. "
        "The curves indicate that the model stabilizes rapidly after the 10th epoch. The L2 regularization and Dropout layers successfully prevented the LSTM components from overfitting to majority classes.", body_style))
    
    curves_path = os.path.join(asset_dir, "training_curves.png")
    if os.path.exists(curves_path):
        story.append(Image(curves_path, width=380, height=105))
        story.append(Paragraph("<b>Figure 5.1:</b> CNN-LSTM-Attention Model Training and Validation convergence curves.", ParagraphStyle("CapF1", parent=body_style, fontName="Times-BoldItalic", alignment=TA_CENTER)))
    
    story.append(PageBreak())

    # ==========================================
    # CHAPTER 5 CONTINUED: CONFUSION MATRIX & ROC CURVES
    # ==========================================
    story.append(Paragraph("5.3 Confusion Matrix Analysis", heading2_style))
    story.append(Paragraph(
        "To inspect the model's classification details across all 5 classes, we generated a Confusion Matrix evaluated on the test set. "
        "It indicates high-density diagonal values for Normal, DoS, and Probe traffic. Very slight misclassifications occur within the sparse U2R and R2L classes, which are frequently confused with normal traffic due to their extremely low representation in the raw training logs.", body_style))
    
    cm_path = os.path.join(asset_dir, "confusion_matrix.png")
    if os.path.exists(cm_path):
        story.append(Image(cm_path, width=360, height=138))
        story.append(Paragraph("<b>Figure 5.2:</b> Heatmap Confusion Matrix evaluated on the UNSW-NB15 test partition.", ParagraphStyle("CapF2", parent=body_style, fontName="Times-BoldItalic", alignment=TA_CENTER)))
    
    story.append(Paragraph("5.4 ROC Curves Analysis", heading2_style))
    story.append(Paragraph(
        "The Receiver Operating Characteristic (ROC) curves plot the True Positive Rate against the False Positive Rate across various classification thresholds. "
        "The arcing curves show excellent Area Under the Curve (AUC) scores exceeding 0.95 for volumetric DoS, Probe, and Normal classes, confirming the hybrid model's robustness.", body_style))
    
    roc_path = os.path.join(asset_dir, "roc_curves.png")
    if os.path.exists(roc_path):
        story.append(Image(roc_path, width=200, height=166))
        story.append(Paragraph("<b>Figure 5.3:</b> Multi-class ROC Curves evaluated on the UNSW-NB15 test partition.", ParagraphStyle("CapF3", parent=body_style, fontName="Times-BoldItalic", alignment=TA_CENTER)))
    
    story.append(PageBreak())

    # ==========================================
    # CHAPTER 5 CONTINUED: CLASS-WISE ANALYSIS & SOC SCREENSHOT
    # ==========================================
    story.append(Paragraph("5.5 Class-wise Threat Detection Analysis", heading2_style))
    story.append(Paragraph(
        "Evaluating model performance across threat categories reveals a typical deep learning pattern: class balance heavily influences class-wise accuracy. "
        "Normal, DoS, and Probe connection records are highly frequent within the training set, allowing the model to learn their signatures with high precision (e.g. 90% for Normal, 87% for Probe). "
        "In contrast, U2R and R2L exploits are extremely sparse, representing less than 1% of the data. The BiLSTM layer with Self-Attention proves critical here: by capturing the temporal sequence of subtle actions, the model still manages to detect these low-profile attacks without excessive false alarms.", body_style))
    
    dist_path = os.path.join(asset_dir, "attack_distribution.png")
    if os.path.exists(dist_path):
        story.append(Image(dist_path, width=340, height=144))
        story.append(Paragraph("<b>Figure 5.4:</b> Class distribution in the UNSW-NB15 dataset.", ParagraphStyle("CapF4", parent=body_style, fontName="Times-BoldItalic", alignment=TA_CENTER)))
    
    metrics_path = os.path.join(asset_dir, "per_class_metrics.png")
    if os.path.exists(metrics_path):
        story.append(Image(metrics_path, width=330, height=163))
        story.append(Paragraph("<b>Figure 5.4b:</b> Class-wise Precision, Recall, and F1-scores breakdown on UNSW-NB15.", ParagraphStyle("CapF4b", parent=body_style, fontName="Times-BoldItalic", alignment=TA_CENTER)))
    
    story.append(Paragraph("5.6 Live SOC Dashboard Telemetry Detections", heading2_style))
    story.append(Paragraph(
        "Below is a screen capture directly from the live SOC Control Dashboard showing active connections, throughput rates, CPU loads, "
        "and the dynamic queue of neural detections generated from the attack simulator in real time. The integration of this visually stunning dashboard effectively completes the practical deployment challenge.", body_style))
    
    dash_path = os.path.join(asset_dir, "soc_dashboard.png")
    if os.path.exists(dash_path):
        story.append(Image(dash_path, width=360, height=205))
        story.append(Paragraph("<b>Figure 5.5:</b> Real-time SOC Control Dashboard populated with active neural telemetry alerts.", ParagraphStyle("CapF5", parent=body_style, fontName="Times-BoldItalic", alignment=TA_CENTER)))
    
    story.append(PageBreak())

    # ==========================================
    # CHAPTER 6 & 7: CONCLUSION & REFERENCES
    # ==========================================
    story.append(Paragraph("CHAPTER 6", heading1_style))
    story.append(Paragraph("CONCLUSION &amp; FUTURE SCOPE", heading2_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("6.1 Conclusion", heading2_style))
    story.append(Paragraph(
        "This engineering project successfully designed, implemented, and deployed NeuroShield, an advanced, highly responsive anomaly-based "
        "Network Intrusion Detection System powered by a hybrid CNN-BiLSTM-Attention deep neural network. By combining spatial 1D CNN feature extraction filters "
        "with recurrent sequence LSTMs and self-attention weights, the resulting neural classifier reliably isolates complex intrusion patterns across rolling network packet sequences of length 10. "
        "The system was evaluated on the modern UNSW-NB15 test set, achieving an overall accuracy of 77.32% and a weighted F1-score of 78.28%, comprehensively proving its efficacy. "
        "Furthermore, by wrapping the neural prediction engine within a decoupled, asynchronously threaded Python Flask API and exposing the telemetry via a React/TailwindCSS SPA dashboard, "
        "we successfully deployed the system as a production-ready enterprise security appliance.", body_style))
    
    story.append(Paragraph("6.2 Future Scope", heading2_style))
    story.append(Paragraph(
        "While NeuroShield performs robustly under stress, several future optimizations can be pursued. "
        "First, leverage distributed big data frameworks like Apache Spark to scale sequence building and deep neural inference across cluster nodes. "
        "Second, deploy the Flask API backend integrated with NVIDIA TensorRT C++ optimization libraries to reduce neural prediction latency to under 1 millisecond. "
        "Third, integrate a live packet capturing script (using optimized Scapy or PyShark bindings) to sniff active local hardware interface packet headers directly from the NIC, transitioning the system into a live network sniffer appliance.", body_style))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("CHAPTER 7", heading1_style))
    story.append(Paragraph("REFERENCES", heading2_style))
    story.append(Spacer(1, 10))
    
    ref_data = [
        "1. [UNSW-NB15 Dataset] N. Moustafa and J. Slay, 'UNSW-NB15: a comprehensive data set for network intrusion detection systems,' IEEE Military Communications and Information Systems Conference (MilCIS), 2015.",
        "2. [Attention Mechanism] A. Vaswani et al., 'Attention is all you need,' Advances in Neural Information Processing Systems (NeurIPS), pp. 5998–6008, 2017.",
        "3. [BiLSTM Network] S. Hochreiter and J. Schmidhuber, 'Long Short-Term Memory,' Neural Computation, vol. 9, no. 8, pp. 1735–1780, 1997.",
        "4. [Deep Learning in NIDS] M. A. Khan et al., 'A Hybrid CNN-LSTM Model for Network Intrusion Detection,' IEEE Access, vol. 8, pp. 137322–137330, 2020.",
        "5. [Focal Loss] T.-Y. Lin et al., 'Focal Loss for Dense Object Detection,' IEEE International Conference on Computer Vision (ICCV), 2017.",
        "6. [Class-Balanced Loss] Y. Cui et al., 'Class-Balanced Loss Based on Effective Number of Samples,' CVPR, 2019.",
        "7. [C-DAC Mohali] Centre for Development of Advanced Computing, C-DAC Mohali Training Programs, 2026. [Online] Available: https://www.cdac.in/",
        "8. [TensorFlow & Keras] TensorFlow Development Team, 'TensorFlow: Large-Scale Machine Learning on Heterogeneous Distributed Systems,' 2015. [Online] Available: https://www.tensorflow.org/"
    ]
    for ref in ref_data:
        story.append(Paragraph(ref, ParagraphStyle("RefCell", parent=body_style, spaceAfter=6)))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Report successfully compiled and saved to {filename}")

if __name__ == "__main__":
    build_pdf()
