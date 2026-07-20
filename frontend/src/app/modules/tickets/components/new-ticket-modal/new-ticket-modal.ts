import { CommonModule } from '@angular/common';
import { Component, EventEmitter, OnDestroy, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule, ImagePlus, X } from 'lucide-angular';
import { Ticket } from '../../../../core/models/ticket.model';

@Component({
  selector: 'app-new-ticket-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  templateUrl: './new-ticket-modal.html',
  styleUrls: ['./new-ticket-modal.css']
})
export class NewTicketModalComponent implements OnDestroy {
  @Output() close = new EventEmitter<void>();
  @Output() create = new EventEmitter<Ticket>();

  readonly ImagePlus = ImagePlus;
  readonly X = X;

  title = '';
  description = '';
  residentName = '';
  apartment = '';
  selectedFileName = '';
  selectedImage?: File;
  imagePreviewUrl?: string;
  imageError = '';
  submitted = false;

  errors = {
    title: '',
    description: '',
    residentName: '',
    apartment: ''
  };

  onClose(): void {
    this.close.emit();
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    this.clearImage();
    this.imageError = '';
    if (!file) {
      return;
    }

    if (!file.type.startsWith('image/')) {
      this.imageError = 'Selecione um arquivo de imagem válido.';
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      this.imageError = 'A imagem deve ter no máximo 10 MB.';
      return;
    }

    this.selectedFileName = file.name;
    this.selectedImage = file;
    this.imagePreviewUrl = URL.createObjectURL(file);
  }

  ngOnDestroy(): void {
    this.clearImage();
  }

  validateForm(): boolean {
    this.errors = {
      title: '',
      description: '',
      residentName: '',
      apartment: ''
    };

    let isValid = true;

    if (!this.title.trim()) {
      this.errors.title = 'Informe o título do chamado.';
      isValid = false;
    } else if (this.title.trim().length < 5) {
      this.errors.title = 'O título deve ter pelo menos 5 caracteres.';
      isValid = false;
    }

    if (!this.description.trim()) {
      this.errors.description = 'Descreva o problema encontrado.';
      isValid = false;
    } else if (this.description.trim().length < 10) {
      this.errors.description = 'A descrição deve ter pelo menos 10 caracteres.';
      isValid = false;
    }

    if (!this.residentName.trim()) {
      this.errors.residentName = 'Informe o nome do morador.';
      isValid = false;
    }

    if (!this.apartment.trim()) {
      this.errors.apartment = 'Informe a unidade do morador.';
      isValid = false;
    }

    return isValid;
  }

  onSubmit(): void {
    this.submitted = true;

    if (!this.validateForm()) {
      return;
    }

    const newTicket: Ticket = {
      id: Date.now(),
      title: this.title.trim(),
      description: this.description.trim(),
      residentName: this.residentName.trim(),
      apartment: this.apartment.trim(),
      status: 'ABERTO',
      createdAt: new Date().toISOString(),
      imageFile: this.selectedImage,
      imageUrl: this.imagePreviewUrl,
      avatarColor: '#8b5cf6'
    };

    this.create.emit(newTicket);
    this.onClose();
  }

  private clearImage(): void {
    if (this.imagePreviewUrl) {
      URL.revokeObjectURL(this.imagePreviewUrl);
    }
    this.selectedFileName = '';
    this.selectedImage = undefined;
    this.imagePreviewUrl = undefined;
  }
}
