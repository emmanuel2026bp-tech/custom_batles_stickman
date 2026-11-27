import pygame

from game_config import TEAM_COLORS
from matchups import get_matchup_label


def draw_combat_hud(
    screen: pygame.Surface,
    *,
    w: int,
    elapsed: float,
    paused: bool,
    terrain_name: str,
    live_a_count: int,
    live_b_count: int,
    font_hud: pygame.font.Font,
) -> tuple[int, int]:
    hud_rect = pygame.Rect(0, 0, w, 34)
    pygame.draw.rect(screen, (18, 20, 26), hud_rect)
    mins = int(elapsed) // 60
    secs = int(elapsed) % 60
    state_txt = "PAUSA" if paused else "COMBATE"
    hud_line = (
        f"{mins:02d}:{secs:02d} | {state_txt} | "
        f"{terrain_name.upper()} | "
        f"A(Amarillo):{live_a_count} vs B(Rojo):{live_b_count} | "
        f"[P] Pausa [R] Terreno [ESC] Editor"
    )
    hud_surf = font_hud.render(hud_line, True, (246, 226, 146))
    screen.blit(hud_surf, (12, 9))
    return mins, secs


def draw_pause_overlay(
    screen: pygame.Surface,
    *,
    w: int,
    h: int,
    mouse_pos: tuple[int, int],
    pause_edit_btn: pygame.Rect,
    pause_resume_btn: pygame.Rect,
    pause_exit_btn: pygame.Rect,
    font_banner: pygame.font.Font,
    font_small: pygame.font.Font,
) -> None:
    veil = pygame.Surface((w, h), pygame.SRCALPHA)
    veil.fill((10, 12, 18, 125))
    screen.blit(veil, (0, 0))

    panel_w, panel_h = min(420, max(280, w - 32)), 126
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(
        panel,
        (22, 25, 36, 205),
        pygame.Rect(0, 0, panel_w, panel_h),
        border_radius=8,
    )
    pygame.draw.rect(
        panel,
        (246, 226, 146, 210),
        pygame.Rect(0, 0, panel_w, panel_h),
        width=2,
        border_radius=8,
    )
    panel_rect = pygame.Rect(
        w // 2 - panel_w // 2, h // 2 - panel_h // 2, panel_w, panel_h
    )
    screen.blit(panel, panel_rect.topleft)

    title_surf = font_banner.render("PAUSA", True, (246, 226, 146))
    screen.blit(
        title_surf,
        (panel_rect.centerx - title_surf.get_width() // 2, panel_rect.y + 14),
    )

    btn_gap = 10
    avail_btn_w = max(180, panel_w - 32 - btn_gap * 2)
    pause_edit_btn.width = max(60, int(avail_btn_w * 0.32))
    pause_resume_btn.width = max(72, int(avail_btn_w * 0.38))
    pause_exit_btn.width = max(
        56, avail_btn_w - pause_edit_btn.width - pause_resume_btn.width
    )
    pause_edit_btn.height = 34
    pause_resume_btn.height = 34
    pause_exit_btn.height = 34

    total_pw = (
        pause_edit_btn.width
        + pause_resume_btn.width
        + pause_exit_btn.width
        + btn_gap * 2
    )
    p_start_x = panel_rect.centerx - total_pw // 2
    p_btn_y = panel_rect.y + 68

    pause_edit_btn.topleft = (p_start_x, p_btn_y)
    pause_resume_btn.topleft = (pause_edit_btn.right + btn_gap, p_btn_y)
    pause_exit_btn.topleft = (pause_resume_btn.right + btn_gap, p_btn_y)

    for r_btn, txt, base_c, hov_c in (
        (pause_edit_btn, "Editar", (58, 66, 92), (82, 94, 128)),
        (pause_resume_btn, "Continuar", (44, 122, 82), (62, 156, 108)),
        (pause_exit_btn, "Salir", (142, 48, 52), (178, 64, 68)),
    ):
        col = hov_c if r_btn.collidepoint(mouse_pos) else base_c
        pygame.draw.rect(screen, col, r_btn, border_radius=6)
        pygame.draw.rect(
            screen, (235, 236, 242), r_btn, width=1, border_radius=6
        )
        t_s = font_small.render(txt, True, (250, 250, 252))
        screen.blit(
            t_s,
            (
                r_btn.centerx - t_s.get_width() // 2,
                r_btn.centery - t_s.get_height() // 2,
            ),
        )


def draw_battle_over_overlay(
    screen: pygame.Surface,
    *,
    w: int,
    h: int,
    mins: int,
    secs: int,
    preset_key: str,
    live_a_count: int,
    live_b_count: int,
    mouse_pos: tuple[int, int],
    edit_btn: pygame.Rect,
    replay_btn: pygame.Rect,
    exit_btn: pygame.Rect,
    font_banner: pygame.font.Font,
    font_hud: pygame.font.Font,
    font_small: pygame.font.Font,
) -> None:
    if live_a_count == 0 and live_b_count == 0:
        win_msg = "EMPATE"
        win_col = (240, 224, 150)
    elif live_a_count > 0:
        win_msg = "VICTORIA EQUIPO A"
        win_col = TEAM_COLORS["A"]
    else:
        win_msg = "VICTORIA EQUIPO B"
        win_col = TEAM_COLORS["B"]

    box_w = min(440, max(280, w - 32))
    box = pygame.Rect(w // 2 - box_w // 2, h // 2 - 68, box_w, 136)
    pygame.draw.rect(screen, (22, 20, 30), box, border_radius=8)
    pygame.draw.rect(screen, win_col, box, width=2, border_radius=8)

    b_surf = font_banner.render(win_msg, True, win_col)
    screen.blit(
        b_surf, (box.centerx - b_surf.get_width() // 2, box.y + 14)
    )
    sub_surf = font_hud.render(
        f"{get_matchup_label(preset_key)} • {mins:02d}:{secs:02d}",
        True,
        (235, 232, 224),
    )
    screen.blit(
        sub_surf, (box.centerx - sub_surf.get_width() // 2, box.y + 50)
    )

    btn_gap = 10
    avail_end_w = max(180, box_w - 32 - btn_gap * 2)
    edit_btn.width = max(64, int(avail_end_w * 0.34))
    replay_btn.width = max(72, int(avail_end_w * 0.36))
    exit_btn.width = max(
        56, avail_end_w - edit_btn.width - replay_btn.width
    )
    edit_btn.height = 34
    replay_btn.height = 34
    exit_btn.height = 34

    total_w = edit_btn.width + replay_btn.width + exit_btn.width + btn_gap * 2
    start_x = box.centerx - total_w // 2
    btn_y = box.y + 84

    edit_btn.topleft = (start_x, btn_y)
    replay_btn.topleft = (edit_btn.right + btn_gap, btn_y)
    exit_btn.topleft = (replay_btn.right + btn_gap, btn_y)

    for r_btn, txt, base_c, hov_c in (
        (edit_btn, "Editar (E)", (58, 66, 92), (82, 94, 128)),
        (replay_btn, "Repetir (R)", (46, 118, 172), (68, 152, 214)),
        (exit_btn, "Salir", (142, 48, 52), (178, 64, 68)),
    ):
        col = hov_c if r_btn.collidepoint(mouse_pos) else base_c
        pygame.draw.rect(screen, col, r_btn, border_radius=6)
        pygame.draw.rect(
            screen, (226, 224, 235), r_btn, width=1, border_radius=6
        )
        t_s = font_small.render(txt, True, (248, 248, 252))
        screen.blit(
            t_s,
            (
                r_btn.centerx - t_s.get_width() // 2,
                r_btn.centery - t_s.get_height() // 2,
            ),
        )