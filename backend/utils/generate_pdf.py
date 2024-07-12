import io

from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_shipment_pdf(shipment):
    # Prepare a buffer to write the PDF to
    buffer = io.BytesIO()

    # Create a canvas
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    p.setTitle(f"Shipment Details {shipment.id}")
    p.setFont("Helvetica-Bold", 14)
    p.drawString(30, height - 40, "Shipment Details")

    # Reset font size
    p.setFont("Helvetica", 10)
    y_position = height - 60

    # Function to write text to PDF and update y_position
    def write_line(text):
        nonlocal y_position
        p.drawString(30, y_position, text)
        y_position -= 20

    # Example data from Shipment object
    write_line("Container Details")  #
    write_line(
        f"Container: {shipment.container.container_number}"
    )  # Assuming Container model has identifiable field
    write_line(f"Container Size: {shipment.container.size}")
    write_line(f"Container Type: {shipment.container.type}")
    write_line(f"Container Type: {shipment.container.owner}")
    write_line(f"Container Chasis Number: {shipment.container.chassis_number}")
    write_line(f"Container Chasis Type: {shipment.container.chassis_type}")
    write_line(f"Container Chasis Size: {shipment.container.chassis_size}")
    write_line(f"Container SCAC: {shipment.container.scac}")
    write_line(f"Container Genset Number: {shipment.container.genset_number}")
    write_line(f"Container Temperature: {shipment.container.temperature}")

    write_line("Customer Details")  #
    if shipment.customer:
        write_line(f"Customer: {shipment.customer.associate_company_name}")
        write_line(f"Customer Name: {shipment.customer.responsible_person_name}")
        write_line(f"Customer Email: {shipment.customer.email}")
        write_line(f"Customer Address: {shipment.customer.address}")
        write_line(f"Customer Phone Number: {shipment.customer.phone}")

    write_line("Driver Details")  #
    write_line(
        f"Driver Name: {shipment.driver.user.first_name} {shipment.driver.user.last_name}"
    )
    write_line(f"Driver Company: {shipment.driver.company_name}")
    write_line(f"Driver Email: {shipment.driver.user.email}")
    write_line(f"Driver Phone Number: {shipment.driver.user.phone_number}")

    write_line("Warehouse Details")  #
    write_line(f"Warehouse: {shipment.warehouse.company.company_name}")
    write_line(
        f"Warehouse Phone Number: {shipment.warehouse.company.company_phone_number}"
    )
    write_line(f"Warehouse Email: {shipment.warehouse.company.company_email}")

    write_line(
        f"Shipment Assigned Date: {shipment.assigned_date.strftime('%Y-%m-%d %H:%M:%S') if shipment.assigned_date else 'N/A'}"
    )

    # Continue for each field you wish to include...
    write_line(f"Pickup Location: {shipment.pickup_location}")
    write_line(f"Delivery Location: {shipment.delivery_location}")
    write_line(f"Return Location: {shipment.return_location}")

    write_line(f"Driver Delivered At: {shipment.driver_delivered_date}")
    write_line(f"Warehouse Receieved At: {shipment.warehouse_accepted_date}")
    # Finalize the PDF
    p.showPage()
    p.save()

    # Move back to the beginning of the StringIO buffer
    buffer.seek(0)

    # Create a Django ContentFile from the buffer
    pdf = ContentFile(buffer.read())

    # Generate a filename
    filename = f"shipment_details_{shipment.id}.pdf"

    # Save the PDF file to the proof_of_delivery_form field of the Shipment instance
    shipment.proof_of_delivery_file.save(filename, pdf)
    # filename = "proof_of_delivery_{}.pdf".format(shipment.id)
    # shipment.proof_of_delivery_file.save(filename, ContentFile(buffer.read()))
    # Make sure to close the buffer
    buffer.close()
