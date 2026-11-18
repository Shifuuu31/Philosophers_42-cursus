/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   philo.h                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: asaadane <asaadane@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/01/02 23:04:00 by asaadane          #+#    #+#             */
/*   Updated: 2024/01/02 23:24:34 by asaadane         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef PHILO_H
# define PHILO_H

# include <pthread.h>
# include <stdio.h>
# include <stdlib.h>
# include <string.h>
# include <unistd.h>
# include <sys/time.h>

# define DEATH "%lld %d died\n"
# define TAKING_FORKS "%lld %d has taken a fork\n"
# define EATING "%lld %d is eating\n"
# define SLEEPING "%lld %d is sleeping\n"
# define THINKING "%lld %d is thinking\n"

# define TRUE 1
# define FALSE 0

typedef enum e_moves
{
	FORK_TAKEN,
	EAT,
	SLEEP,
	THINK,
	DIE
}	t_moves;

typedef struct s_info
{
	int					id;
	int					t_eat;
	int					t_sleep;
	int					t_die;
	int					eating_time;
	long long			last_meal;
	long long			start;
	pthread_mutex_t		*left_fork;
	pthread_mutex_t		*right_fork;
	pthread_mutex_t		*sync;
}	t_info;

typedef struct s_philo
{
	int				n_philo;
	int				t_die;
	int				t_eat;
	int				t_sleep;
	int				nbr_meals;
	int				philo_eaft_time;
	int				err;
	long long		start;
	t_info			*philo;
	pthread_mutex_t	*forks;
	pthread_mutex_t	sync;
}	t_philo;

// Parsing & Validation
int			parsing(char **args, int args_num, t_philo *target);

// Routine & Actions
void		eat(t_info *philo);
void		philo_sleep(t_info *philo);
void		philo_think(t_info *philo);
void		manage_philos(t_info *philo, t_moves action);

// Monitor & State
int			check_philos(t_philo *info);

// Utilities & Time
int			ft_isdigit(int c);
int			ft_atoi(const char *str);
long long	ft_time(void);
void		ft_usleep(unsigned long long time);
void		clean_data(t_philo *info);

#endif
