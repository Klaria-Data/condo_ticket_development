import { CommonModule } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommentsService, Comment } from '../../../../core/services/comments.service';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-ticket-comments',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './ticket-comments.html',
  styleUrls: ['./ticket-comments.css'],
})
export class TicketCommentsComponent implements OnInit {
  @Input() ticketId!: number;

  comments: Comment[] = [];
  commentForm: FormGroup;
  loading = false;
  errorMessage: string | null = null;
  isAuthenticated = false;
  currentUserName = '';

  constructor(
    private readonly commentsService: CommentsService,
    private readonly authService: AuthService,
    private readonly fb: FormBuilder,
  ) {
    this.commentForm = this.fb.group({
      mensagem: ['', [Validators.required, Validators.minLength(1), Validators.maxLength(2000)]],
    });
  }

  ngOnInit(): void {
    this.loadComments();
    this.checkAuthentication();
  }

  private checkAuthentication(): void {
    const user = this.authService.getCurrentUser();
    this.isAuthenticated = !!user;
    this.currentUserName = user?.nome || '';
  }

  private loadComments(): void {
    this.loading = true;
    this.errorMessage = null;

    this.commentsService.getTicketComments(this.ticketId).subscribe({
      next: (comments: Comment[]) => {
        this.comments = comments;
        this.loading = false;
      },
      error: (err: unknown) => {
        console.error('Erro ao carregar comentários:', err);
        // Não exibe erro - comentários são opcionais
        this.loading = false;
      },
    });
  }

  onSubmit(): void {
    if (!this.commentForm.valid || !this.isAuthenticated) {
      return;
    }

    const payload = this.commentForm.value;
    this.commentsService.createComment(this.ticketId, payload).subscribe({
      next: (newComment: Comment) => {
        this.comments.push(newComment);
        this.commentForm.reset();
        this.errorMessage = null;
      },
      error: (err: unknown) => {
        console.error('Erro ao criar comentário:', err);
        this.errorMessage = 'Falha ao enviar comentário.';
      },
    });
  }

  getInitials(name: string | null): string {
    if (!name) return '?';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  }
}

