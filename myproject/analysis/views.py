import os
import uuid
import pandas as pd
import chardet
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import tempfile
from django.core.exceptions import ValidationError
from django.shortcuts import render
from .forms import UploadForm
from django.http import HttpResponse
from django.template.utils import get_app_template_dirs
from django.shortcuts import render


def upload_csv(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            age = form.cleaned_data['age']

            uploaded_file = request.FILES['csv_file']
            max_file_size = 10 * 1024 * 1024
            if uploaded_file.size > max_file_size:
                raise ValidationError(f"File size exceeds maximum limit of {max_file_size} bytes.")

            # Use tempfile for secure temp file handling
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            try:
                # Determine file type and read it
                if uploaded_file.name.endswith('.csv'):
                    with open(temp_file_path, 'rb') as f:
                        result = chardet.detect(f.read())
                    encoding = result['encoding']
                    try:
                        df = pd.read_csv(temp_file_path, encoding=encoding)
                    except UnicodeDecodeError:
                        df = pd.read_csv(temp_file_path, encoding='iso-8859-1')
                elif uploaded_file.name.endswith('.xlsx'):
                    df = pd.read_excel(temp_file_path, engine='openpyxl')
                elif uploaded_file.name.endswith('.xls'):
                    df = pd.read_excel(temp_file_path, engine='xlrd')
                else:
                    raise ValidationError("Unsupported file type. Please upload a CSV or Excel file.")

                # Calculate summary statistics
                numerical_columns = df.select_dtypes(include=['int64', 'float64'])
                summary_stats = numerical_columns.describe(percentiles=[.25, .50, .75])

                # Calculate median separately for each numerical column
                median_values = numerical_columns.median()
                for col in numerical_columns:
                    summary_stats.at['50%', col] = median_values[col]

                # Generate histograms and encode them as base64
                plot_data_dict = {}
                for col in numerical_columns:
                    fig, ax = plt.subplots()
                    ax.hist(df[col])
                    ax.set_xlabel(col)
                    ax.set_ylabel('Frequency')
                    ax.set_title(f'Histogram of {col}')

                    buffer = BytesIO()
                    fig.savefig(buffer, format='png')
                    buffer.seek(0)
                    plot_data = base64.b64encode(buffer.read()).decode('utf-8')
                    buffer.close()
                    plt.close(fig)

                    plot_data_dict[col] = plot_data

            except FileNotFoundError:
                raise ValidationError("Uploaded file not found. Please try again.")
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

            context = {
                'name': name,
                'email': email,
                'age': age,
                'summary_stats': summary_stats.to_dict(),
                'plot_data_dict': plot_data_dict,
                'form': form
            }

            return render(request, 'sucess.html', context)
    else:
        form = UploadForm()
    
    return render(request, 'upload_form.html', {'form': form})




def debug_template_dirs(request):
    # Get template directories
    dirs = get_app_template_dirs('django')
    # Create a response with template directories
    response_content = "<br>".join(dirs)
    return HttpResponse(f"Template directories:<br>{response_content}") 