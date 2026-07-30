import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, Input, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommentsService, Comment } from '../../../../core/services/comments.service';
import { AuthService } from '../../../../core/services/auth.service';

/**
 * Componente de chat/comentários de um ticket.
 *
 * Exibe a lista de comentários em ordem cronológica e permite que usuários
 * autenticados adicionem novas mensagens.
 *
 * Permissões de edição/deleção:
 *   - Botões "Editar" e "Excluir" são exibidos apenas para comentários
 *     cujo autor é o usuário logado (verificado pelo usuario_id).
 *   - O backend também valida as permissões, retornando 403 se necessário.
 */
@Component({
  selector: 'app-ticket-comments',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  templateUrl: './ticket-comments.html',
  styleUrls: ['./ticket-comments.css'],
})
export class TicketCommentsComponent implements OnInit {
  /** ID do ticket cujos comentários serão exibidos. */
  @Input() ticketId!: number;

  comments: Comment[] = [];
  commentForm: FormGroup;

  loading = false;
  errorMessage: string | null = null;

  isAuthenticated = false;
  currentUserName = '';
  currentUserId: number | null = null;

  /** ID do comentário em edição (null = nenhum em edição). */
  editingCommentId: number | null = null;
  /** Conteúdo temporário durante a edição. */
  editingMessage = '';

  constructor(
    private readonly commentsService: CommentsService,
    private readonly authService: AuthService,
    private readonly fb: FormBuilder,
    private readonly cdr: ChangeDetectorRef,
  ) {
    this.commentForm = this.fb.group({
      mensagem: ['', [Validators.required, Validators.minLength(1), Validators.maxLength(2000)]],
    });
  }

  ngOnInit(): void {
    this.checkAuthentication();
    this.loadComments();
  }

  /** Verifica se o usuário está autenticado e armazena seu ID para controle de permissões. */
  private checkAuthentication(): void {
    const user = this.authService.getCurrentUser();
    this.isAuthenticated = !!user;
    this.currentUserName = user?.nome ?? '';
    this.currentUserId = user?.id ?? null;
  }

  /** Carrega os comentários do ticket via API. */
  private loadComments(): void {
    this.loading = true;
    this.errorMessage = null;

    this.commentsService.getTicketComments(this.ticketId).subscribe({
      next: (comments: Comment[]) => {
        this.comments = comments;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'Falha ao carregar os comentários deste chamado.';
        this.cdr.detectChanges();
      },
    });
  }

  /** Envia um novo comentário. */
  onSubmit(): void {
    if (!this.commentForm.valid || !this.isAuthenticated) {
      return;
    }

    const payload = this.commentForm.value as { mensagem: string };
    this.commentsService.createComment(this.ticketId, payload).subscribe({
      next: (newComment: Comment) => {
        this.comments = [...this.comments, newComment];
        this.commentForm.reset();
        this.errorMessage = null;
        this.cdr.detectChanges();
      },
      error: () => {
        this.errorMessage = 'Falha ao enviar comentário.';
        this.cdr.detectChanges();
      },
    });
  }

  /** Retorna true se o comentário pertence ao usuário logado. */
  isOwnComment(comment: Comment): boolean {
    return this.currentUserId !== null && comment.usuario_id === this.currentUserId;
  }

  /** Entra no modo de edição para o comentário informado. */
  startEdit(comment: Comment): void {
    this.editingCommentId = comment.id;
    this.editingMessage = comment.mensagem;
  }

  /** Cancela a edição em andamento sem salvar. */
  cancelEdit(): void {
    this.editingCommentId = null;
    this.editingMessage = '';
  }

  /** Salva as alterações do comentário em edição. */
  saveEdit(comment: Comment): void {
    if (!this.editingMessage.trim()) {
      return;
    }

    this.commentsService
      .updateComment(this.ticketId, comment.id, { mensagem: this.editingMessage })
      .subscribe({
        next: (updated: Comment) => {
          this.comments = this.comments.map((c) => (c.id === comment.id ? updated : c));
          this.cancelEdit();
          this.errorMessage = null;
          this.cdr.detectChanges();
        },
        error: () => {
          this.errorMessage = 'Falha ao editar comentário.';
          this.cdr.detectChanges();
        },
      });
  }

  /** Remove o comentário após confirmação do usuário. */
  deleteComment(commentId: number): void {
    if (!confirm('Tem certeza que deseja remover este comentário?')) {
      return;
    }

    this.commentsService.deleteComment(this.ticketId, commentId).subscribe({
      next: () => {
        this.comments = this.comments.filter((c) => c.id !== commentId);
        this.errorMessage = null;
        this.cdr.detectChanges();
      },
      error: () => {
        this.errorMessage = 'Falha ao remover comentário.';
        this.cdr.detectChanges();
      },
    });
  }

  /** Gera as iniciais de um nome para exibir no avatar. */
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
