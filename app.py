"""
Flask web application for Food Product Scanner
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import sys
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Force UTF-8 encoding for stdout and stderr to handle emojis on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from datetime import datetime
from io import BytesIO

app = Flask(__name__)

# Import configuration
try:
    from config import Config
    app.secret_key = Config.SERVICE_SECRET_KEY if hasattr(Config, 'SERVICE_SECRET_KEY') else getattr(Config, 'SECRET_KEY', os.urandom(24))
    app.config['DEBUG'] = Config.DEBUG
except ImportError:
    # Fallback if config not available
    app.secret_key = os.urandom(24)
    app.config['DEBUG'] = True

# Configure session
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# Import food scanner components
try:
    from food_scanner import scanFoodProductSmart as scanFoodProduct
except ImportError:
    from food_scanner import scanFoodProduct
    logger.warning("Using original scanner - smart scanner not available")

# Enhanced user database with multiple user types
users = {
    "admin": generate_password_hash("admin123"),
    "user": generate_password_hash("user123"),
    "demo": generate_password_hash("demo123"),
    "guest": generate_password_hash("guest123")
}

# User roles and permissions
user_roles = {
    "admin": {"role": "Administrator", "permissions": ["full_access", "user_management", "settings"]},
    "user": {"role": "Regular User", "permissions": ["scan", "history", "reports"]},
    "demo": {"role": "Demo User", "permissions": ["scan", "history", "reports", "demo_data"]},
    "guest": {"role": "Guest", "permissions": ["scan", "limited_reports"]}
}

# Scan history storage (in production, use a database)
scan_history = []
# Store full scan results for PDF generation
scan_results_cache = {}


@app.route('/')
def index():
    """Redirect to dashboard"""
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    username = 'Guest'
    user_role = 'User'
    return render_template('dashboard.html', username=username, user_role=user_role)


@app.route('/scan', methods=['POST'])
def scan_product():
    """Scan a food product"""
    try:
        # Handle JSON requests (for barcode scan or other JSON APIs)
        if request.is_json or (request.content_type and 'application/json' in request.content_type):
            data = request.get_json()
            if data.get('type') == 'barcode' or data.get('barcode'):
                barcode = data.get('barcode')
                if not barcode:
                    return jsonify({'success': False, 'error': 'No barcode provided'}), 400
                    
                print(f"Scanning barcode directly: {barcode}")
                result = scanFoodProduct(barcode=barcode)
                
                # Add to history
                scan_id = len(scan_history) + 1
                scan_record = {
                    'id': scan_id,
                    'timestamp': datetime.now().isoformat(),
                    'product_name': result['dashboard']['Product Name'],
                    'brand': result['dashboard']['Brand'],
                    'veg_status': result['dashboard']['Veg Status'],
                    'safety_color': result['dashboard']['Safety Color'],
                    'safety_score': result['dashboard']['Safety Score'],
                    'image_url': result.get('open_food_facts', {}).get('image_url'),
                    'nutriscore': result.get('open_food_facts', {}).get('nutriscore'),
                    'username': 'Guest'
                }
                scan_history.append(scan_record)
                
                # Store full result for PDF generation
                scan_results_cache[scan_id] = result
                
                return jsonify({
                    'success': True,
                    'result': result['dashboard'],
                    'scan_id': scan_id,
                    'pdf_available': True,
                    'open_food_facts': result.get('open_food_facts', {}),
                    'ai_analysis': result.get('ai_analysis', {})
                })
            
            elif data.get('type') == 'camera':
                # No image provided, run dummy camera scan
                result = scanFoodProduct()
                scan_id = len(scan_history) + 1
                scan_record = {
                    'id': scan_id,
                    'timestamp': datetime.now().isoformat(),
                    'product_name': result['dashboard']['Product Name'],
                    'brand': result['dashboard']['Brand'],
                    'veg_status': result['dashboard']['Veg Status'],
                    'safety_color': result['dashboard']['Safety Color'],
                    'safety_score': result['dashboard']['Safety Score'],
                    'username': 'Guest'
                }
                scan_history.append(scan_record)
                scan_results_cache[scan_id] = result
                return jsonify({
                    'success': True,
                    'result': result['dashboard'],
                    'scan_id': scan_id,
                    'pdf_available': True,
                    'ai_analysis': result.get('ai_analysis', {})
                })

        # Handle image upload from file upload
        if 'image' in request.files:
            image_file = request.files['image']
            req_type = request.form.get('type', 'upload')
            
            if image_file.filename != '':
                import tempfile
                import os
                from werkzeug.utils import secure_filename
                
                temp_dir = tempfile.gettempdir()
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(temp_dir, filename)
                image_file.save(image_path)
                
                print(f"Processing image upload (type={req_type}): {image_path}")
                
                try:
                    # Pass the temporary image path to our scanner
                    result = scanFoodProduct(image_path=image_path)
                    
                    print(f"Scan result: {result['dashboard']['Product Name']}")
                    
                    # Add to history
                    scan_id = len(scan_history) + 1
                    scan_record = {
                        'id': scan_id,
                        'timestamp': datetime.now().isoformat(),
                        'product_name': result['dashboard']['Product Name'],
                        'brand': result['dashboard']['Brand'],
                        'veg_status': result['dashboard']['Veg Status'],
                        'safety_color': result['dashboard']['Safety Color'],
                        'safety_score': result['dashboard']['Safety Score'],
                        'image_url': result.get('open_food_facts', {}).get('image_url'),
                        'nutriscore': result.get('open_food_facts', {}).get('nutriscore'),
                        'username': 'Guest'
                    }
                    scan_history.append(scan_record)
                    
                    # Store full result for PDF generation
                    scan_results_cache[scan_id] = result
                    
                    return jsonify({
                        'success': True,
                        'result': result['dashboard'],
                        'scan_id': scan_id,
                        'pdf_available': True,
                        'open_food_facts': result.get('open_food_facts', {}),
                        'ai_analysis': result.get('ai_analysis', {})
                    })
                finally:
                    # Clean up temporary file
                    if os.path.exists(image_path):
                        os.remove(image_path)
        
        # Handle manual JSON data if form data
        data = request.form.to_dict()
        if data.get('test_mode') or data.get('ingredients'):
            ingredients = request.form.getlist('ingredients') or data.get('ingredients', '').split(',')
            product_name = data.get('product_name', 'Test Product')
            
            result = scanFoodProductTest(
                product_name=product_name,
                ingredients=[i.strip() for i in ingredients if i.strip()]
            )
            
            # Add to history
            scan_id = len(scan_history) + 1
            scan_record = {
                'id': scan_id,
                'timestamp': datetime.now().isoformat(),
                'product_name': result['dashboard']['Product Name'],
                'brand': result['dashboard']['Brand'],
                'veg_status': result['dashboard']['Veg Status'],
                'safety_color': result['dashboard']['Safety Color'],
                'safety_score': result['dashboard']['Safety Score'],
                'username': 'Guest'
            }
            scan_history.append(scan_record)
            scan_results_cache[scan_id] = result
            
            return jsonify({
                'success': True,
                'result': result['dashboard'],
                'scan_id': scan_id,
                'pdf_available': True,
                'ai_analysis': result.get('ai_analysis', {})
            })
            
        return jsonify({'success': False, 'error': 'Invalid request or missing files'}), 400
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in scan_product: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'success': False, 'error': f'Scanning error: {str(e)}'}), 500
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in scan_product: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'success': False, 'error': f'Scanning error: {str(e)}'}), 500


@app.route('/scan/<int:scan_id>')
def scan_details(scan_id):
    """View details of a specific scan"""
    scan = next((s for s in scan_history if s['id'] == scan_id), None)
    if not scan:
        return redirect(url_for('history'))
    
    return render_template('scan_details.html', scan=scan)


@app.route('/history')
def history():
    """Scan history dashboard"""
    user_scans = scan_history
    return render_template('history.html', scans=user_scans, username='Guest')


@app.route('/api/history')
def api_history():
    """API endpoint for scan history"""
    return jsonify(scan_history)


@app.route('/api/scan/<int:scan_id>')
def api_scan_details(scan_id):
    """API endpoint to get full cached scan details by ID"""
    if scan_id in scan_results_cache:
        return jsonify({
            'success': True,
            'result': scan_results_cache[scan_id]
        })
    
    # If not in cache, let's look in history and construct a minimal result
    scan = next((s for s in scan_history if s['id'] == scan_id), None)
    if scan:
        return jsonify({
            'success': True,
            'result': {
                'dashboard': {
                    'Product Name': scan['product_name'],
                    'Brand': scan['brand'],
                    'Veg Status': scan['veg_status'],
                    'Safety Color': scan['safety_color'],
                    'Safety Score': scan['safety_score'],
                    'Ingredients': ['Water', 'Sugar', 'Natural Flavors'],  # Fallback list
                    'Health Warnings': []
                },
                'open_food_facts': {
                    'barcode': None,
                    'image_url': scan.get('image_url'),
                    'nutriscore': scan.get('nutriscore')
                }
            }
        })
    return jsonify({'success': False, 'error': 'Scan result not found'}), 404



@app.route('/profile')
def profile():
    """User profile page"""
    user_scans = scan_history
    stats = {
        'total_scans': len(user_scans),
        'avg_safety_score': sum(s['safety_score'] for s in user_scans) / len(user_scans) if user_scans else 0,
        'veg_products': len([s for s in user_scans if s['veg_status'] in ['Vegan', 'Vegetarian']]),
        'red_products': len([s for s in user_scans if s['safety_color'] == 'RED'])
    }
    return render_template('profile.html', username='Guest', stats=stats)


@app.route('/test/scanner')
def test_scanner():
    """Test scanner without image"""
    try:
        result = scanFoodProduct()
        return jsonify({
            'success': True,
            'product': result['dashboard']['Product Name'],
            'brand': result['dashboard']['Brand'],
            'safety': result['dashboard']['Safety Color']
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/download/pdf/<int:scan_id>')
def download_pdf(scan_id):
    """Download PDF report for a scan"""
    try:
        # Get scan result from cache
        if scan_id not in scan_results_cache:
            return jsonify({'success': False, 'error': 'Scan not found'}), 404
        
        result = scan_results_cache[scan_id]
        
        # Generate PDF using reportlab
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        # Title
        story.append(Paragraph("🍎 Food Product Analysis Report", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Timestamp
        timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        story.append(Paragraph(f"<i>Generated: {timestamp}</i>", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Product Information
        story.append(Paragraph("Product Information", heading_style))
        dashboard = result['dashboard']
        
        product_data = [
            ['Product Name:', dashboard['Product Name']],
            ['Brand:', dashboard['Brand']],
            ['Vegetarian Status:', dashboard['Veg Status']],
            ['Safety Rating:', f"{dashboard['Safety Color']} ({dashboard['Safety Score']}/100)"]
        ]
        
        product_table = Table(product_data, colWidths=[2*inch, 4.5*inch])
        product_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1'))
        ]))
        story.append(product_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Ingredients
        story.append(Paragraph(f"Ingredients ({len(dashboard['Ingredients'])})", heading_style))
        
        ingredients_text = ", ".join(dashboard['Ingredients'])
        story.append(Paragraph(ingredients_text, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Health Warnings
        if dashboard['Health Warnings']:
            story.append(Paragraph("⚠️ Health Warnings", heading_style))
            
            warning_data = [['Ingredient', 'Conditions']]
            for warning in dashboard['Health Warnings']:
                conditions = ', '.join(warning['conditions'])
                warning_data.append([warning['ingredient'], conditions])
            
            warning_table = Table(warning_data, colWidths=[2*inch, 4.5*inch])
            warning_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fecaca')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#991b1b')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fef2f2')])
            ]))
            story.append(warning_table)
            story.append(Spacer(1, 0.3*inch))
        else:
            story.append(Paragraph("✅ No health warnings detected", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # AI Analysis (if available)
        ai_analysis = result.get('ai_analysis', {})
        if ai_analysis and ai_analysis.get('expert_summary'):
            story.append(Paragraph("🤖 AI Expert Analysis", heading_style))
            story.append(Paragraph(ai_analysis['expert_summary'], styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            if ai_analysis.get('health_benefits'):
                story.append(Paragraph("<b>Health Benefits:</b>", styles['Normal']))
                for benefit in ai_analysis['health_benefits'][:3]:
                    story.append(Paragraph(f"• {benefit}", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
            
            if ai_analysis.get('usage_recommendations'):
                story.append(Paragraph(f"<b>Usage:</b> {ai_analysis['usage_recommendations']}", styles['Normal']))
            
            if ai_analysis.get('storage_recommendations'):
                story.append(Paragraph(f"<b>Storage:</b> {ai_analysis['storage_recommendations']}", styles['Normal']))
            
            story.append(Spacer(1, 0.3*inch))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6b7280'),
            alignment=TA_CENTER
        )
        story.append(Paragraph("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", footer_style))
        story.append(Paragraph("<i>This report is generated by AI analysis and should not replace professional medical advice.</i>", footer_style))
        story.append(Paragraph("<i>Always consult with healthcare professionals for specific dietary concerns.</i>", footer_style))
        story.append(Paragraph(f"<i>Food Product Scanner • Powered by Gemini AI • {timestamp}</i>", footer_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{dashboard['Product Name'].replace(' ', '_')}_Analysis_Report.pdf"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/nutri-score/calculate', methods=['POST'])
def api_calculate_nutri_score():
    """Endpoint for manual Nutri-Score calculation"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        def get_float(key, default=0.0):
            val = data.get(key, default)
            try:
                return float(val) if val is not None else default
            except (ValueError, TypeError):
                return default

        # Map category parameter to NutriScoreCategory enum
        from nutriscore import calculate_nutri_score, NutriScoreCategory
        
        category_str = data.get('category') or 'general_foods'
        try:
            category = NutriScoreCategory(category_str)
        except ValueError:
            # Fallback to old boolean flags mapping if category string is invalid or not provided
            is_beverage = data.get('is_beverage', False) == True or str(data.get('is_beverage', '')).lower() == 'true'
            is_cheese = data.get('is_cheese', False) == True or str(data.get('is_cheese', '')).lower() == 'true'
            is_fat_oil = data.get('is_fat_oil', False) == True or str(data.get('is_fat_oil', '')).lower() == 'true'
            
            if is_cheese:
                category = NutriScoreCategory.CHEESE
            elif is_beverage:
                category = NutriScoreCategory.BEVERAGE
            elif is_fat_oil:
                category = NutriScoreCategory.FATS_OILS_NUTS
            else:
                category = NutriScoreCategory.GENERAL_FOODS

        energy_kj = get_float('energy_kj')
        # If energy is provided in kcal, convert to kJ
        energy_unit = data.get('energy_unit', 'kj')
        if energy_unit == 'kcal':
            energy_kj = energy_kj * 4.184
        
        result = calculate_nutri_score(
            energy_kj=energy_kj,
            sat_fat=get_float('sat_fat'),
            sugars=get_float('sugars'),
            salt=get_float('salt'),
            fiber=get_float('fiber'),
            protein=get_float('protein'),
            fruit_veg_percentage=get_float('fruit_veg_percentage'),
            category=category
        )
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        import traceback
        print(f"Error in api_calculate_nutri_score: {e}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
