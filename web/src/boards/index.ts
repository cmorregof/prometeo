import type { Board, BoardCuadratura, BoardEuclides, BoardQuinto, Frame } from '../types'
import { EuclidesBoard } from './euclides'
import { CuadraturaBoard } from './cuadratura'
import { QuintoBoard } from './quinto'

export interface BoardView {
  /** Redibuja. `animate` es falso tras un salto (línea de tiempo, URL). */
  update(board: Board, f: Frame, animate: boolean): void
  /** Línea de estado (HTML) sobre el tablero. */
  headline(board: Board): string
  setHideWorld?(v: boolean): void
}

export function isEuclides(b: Board): b is BoardEuclides {
  return 'history' in b
}
export function isCuadratura(b: Board): b is BoardCuadratura {
  return 'S' in b
}
export function isQuinto(b: Board): b is BoardQuinto {
  return 'chords' in b
}

export function makeBoard(sample: Board, host: HTMLElement): BoardView {
  if (isEuclides(sample)) return new EuclidesBoard(host)
  if (isCuadratura(sample)) return new CuadraturaBoard(host)
  if (isQuinto(sample)) return new QuintoBoard(host)
  throw new Error('tablero desconocido')
}
